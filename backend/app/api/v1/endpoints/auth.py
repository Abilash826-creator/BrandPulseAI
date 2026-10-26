import uuid
import secrets
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.database import get_db, clean_doc, clean_docs
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_firebase_id_token,
    is_old_hash
)
import logging
from app.schemas.all_schemas import UserCreate, UserLogin, UserResponse, Token, AuthLogResponse, FirebaseUserAuth
from app.core.firewall import security_firewall, extract_client_ip

logger = logging.getLogger("brandpulse.auth")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def set_refresh_token_cookie(response: Response, refresh_token: str, request: Optional[Request] = None):
    """
    Sets httpOnly, SameSite refresh token cookie on the response.
    Only marks 'secure=True' if running over HTTPS.
    """
    is_secure = False
    if request:
        proto = request.headers.get("x-forwarded-proto", "").lower()
        is_secure = request.url.scheme == "https" or proto == "https"
    elif settings.FRONTEND_URL and settings.FRONTEND_URL.startswith("https://"):
        is_secure = True

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/"
    )

async def record_auth_event(db, user_dict: dict, request: Optional[Request], method: str, status_val: str = "AUTHENTICATED"):
    """
    Records an authenticated login event into MongoDB 'auth_logs' collection.
    """
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        client_ip = "127.0.0.1"
        user_agent = "Browser/WebClient"
        if request:
            client_ip = extract_client_ip(request)
            user_agent = request.headers.get("user-agent", "Browser/WebClient")

        log_doc = {
            "id": f"auth_{uuid.uuid4().hex[:10]}",
            "user_id": user_dict.get("id", "unknown"),
            "email": user_dict.get("email", "unknown"),
            "full_name": user_dict.get("full_name", "User"),
            "role": user_dict.get("role", "brand_manager"),
            "status": status_val,
            "login_date": now.strftime("%Y-%m-%d"),
            "login_time": now.strftime("%H:%M:%S"),
            "login_timestamp": now,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "auth_method": method
        }
        await db["auth_logs"].insert_one(log_doc)

        # Update last login info on the user document
        await db["users"].update_one(
            {"id": user_dict.get("id")},
            {
                "$set": {
                    "last_login": now.isoformat(),
                    "last_login_ip": client_ip,
                    "last_login_user_agent": user_agent
                },
                "$inc": {"login_count": 1}
            }
        )
    except Exception as e:
        logger.warning(f"[Auth Audit Warning] Could not write auth log: {e}")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db = get_db()
    user = await db["users"].find_one({"id": user_id})
    if not user or not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_role(required_role: str):
    """
    Dependency that ensures the authenticated user possesses the required role.
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: '{required_role}'"
            )
        return current_user
    return role_checker

@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, request: Request, response: Response):
    # WAF Firewall Inspection
    payload = user_in.model_dump()
    is_safe, threat_type, threat_msg, _ = await security_firewall.inspect_payload(
        request, payload, endpoint_name="/api/v1/auth/register"
    )
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"[WAF Firewall Blocked] {threat_msg}"
        )

    db = get_db()
    normalized_email = user_in.email.strip().lower()
    existing = await db["users"].find_one({"email": normalized_email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    default_brand_id = f"brand_{uuid.uuid4().hex[:8]}"
    
    # Server sets role: new users get "owner"
    assigned_role = "owner"
    
    user_doc = {
        "id": user_id,
        "email": normalized_email,
        "full_name": user_in.full_name.strip(),
        "role": assigned_role,
        "organization": user_in.organization,
        "hashed_password": get_password_hash(user_in.password),
        "is_active": True,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "brand_ids": [default_brand_id],
        "login_count": 1,
        "last_login": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    await db["users"].insert_one(user_doc)

    # Create default local business workspace for the user
    org_name = user_in.organization or (user_in.full_name + "'s Business")
    clean_tag = ''.join(c for c in org_name if c.isalnum()) or "MyBusiness"
    brand_doc = {
        "id": default_brand_id,
        "owner_id": user_id,
        "name": f"{org_name}",
        "business_type": "retail",
        "industry": "Local Business",
        "description": f"Business workspace for {user_in.full_name}.",
        "locations": [
            {
                "id": f"loc_{uuid.uuid4().hex[:6]}",
                "name": "Main Branch",
                "address": "",
                "city": "",
                "phone": "",
                "google_place_id": "",
                "is_primary": True
            }
        ],
        "topics": ["Product Quality", "Price & Discounts", "Staff Behavior", "Store Cleanliness", "Stock Availability", "Billing Speed"],
        "products": [],
        "keywords": [org_name],
        "hashtags": [f"#{clean_tag}"],
        "social_handles": {},
        "competitors": [], # Neutral empty defaults
        "crisis_threshold_negative": 0.35,
        "is_primary": True,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    await db["brands"].insert_one(brand_doc)

    # Record Auth Log
    await record_auth_event(db, user_doc, request, method="registration")
    
    client_ip = security_firewall._extract_client_ip(request)
    security_firewall.record_successful_auth(client_ip)

    access_token = create_access_token(subject=user_id, role=assigned_role)
    refresh_token = create_refresh_token(subject=user_id)
    set_refresh_token_cookie(response, refresh_token, request)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**clean_doc(user_doc)),
        "refresh_token": refresh_token
    }

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request, response: Response):
    client_ip = security_firewall._extract_client_ip(request)
    
    # 1. WAF Deep Packet & Payload Inspection
    payload = credentials.model_dump()
    is_safe, threat_type, threat_msg, _ = await security_firewall.inspect_payload(
        request, payload, endpoint_name="/api/v1/auth/login"
    )
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"[Security Firewall Blocked] {threat_msg}"
        )

    db = get_db()
    normalized_email = credentials.email.strip().lower()
    user = await db["users"].find_one({"email": normalized_email})
    stored_hash = user.get("hashed_password", "") if user else ""
    
    if not user or not verify_password(credentials.password, stored_hash):
        rate_info = security_firewall.record_failed_attempt(client_ip)
        warning = ""
        if rate_info.get("quarantined"):
            warning = f" | IP QUARANTINED for {rate_info.get('quarantine_seconds')}s due to multiple failed attempts."
        elif "remaining_attempts" in rate_info:
            warning = f" | {rate_info['remaining_attempts']} attempts remaining before firewall lockout."

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password{warning}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password Migration: If stored hash is in legacy PBKDF2 format, upgrade to bcrypt
    if is_old_hash(stored_hash):
        new_hash = get_password_hash(credentials.password)
        await db["users"].update_one(
            {"id": user["id"]},
            {"$set": {"hashed_password": new_hash}}
        )
        user["hashed_password"] = new_hash

    # Reset IP rate limit on successful authentication
    security_firewall.record_successful_auth(client_ip)

    # Record Auth Log in MongoDB
    await record_auth_event(db, user, request, method="credentials")

    access_token = create_access_token(subject=user["id"], role=user.get("role", "owner"))
    refresh_token = create_refresh_token(subject=user["id"])
    set_refresh_token_cookie(response, refresh_token, request)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**clean_doc(user)),
        "refresh_token": refresh_token
    }

@router.post("/demo-login", response_model=Token)
async def demo_login(request: Request, response: Response):
    """
    Fixed 1-click login for demo / evaluation with rate limiting defense.
    Disabled when DEMO_MODE is false. Always logs into a fixed demo owner account.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in this environment"
        )

    client_ip = security_firewall._extract_client_ip(request)
    
    # WAF Inspection
    is_safe, threat_type, threat_msg, _ = await security_firewall.inspect_payload(
        request, {"auth_method": "demo_login"}, endpoint_name="/api/v1/auth/demo-login"
    )
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"[Security Firewall Blocked] {threat_msg}"
        )

    db = get_db()
    demo_email = "demo_owner@brandpulse.ai"
    user = await db["users"].find_one({"email": demo_email})
    
    if not user:
        user_id = "user_demo_owner"
        # Generate an unguessable random password for the demo user
        random_password = secrets.token_urlsafe(32)
        default_brand_id = "brand_demo_owner_default"
        user_doc = {
            "id": user_id,
            "email": demo_email,
            "full_name": "Demo Business Owner",
            "role": "owner",
            "organization": "Sri Murugan Bakery & Cafe",
            "hashed_password": get_password_hash(random_password),
            "is_active": True,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "brand_ids": [default_brand_id]
        }
        await db["users"].insert_one(user_doc)
        user = user_doc

    security_firewall.record_successful_auth(client_ip)
    await record_auth_event(db, user, request, method="demo_login_owner")

    access_token = create_access_token(subject=user["id"], role="owner")
    refresh_token = create_refresh_token(subject=user["id"])
    set_refresh_token_cookie(response, refresh_token, request)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**clean_doc(user)),
        "refresh_token": refresh_token
    }

@router.post("/firebase-login", response_model=Token)
async def firebase_login(auth_data: FirebaseUserAuth, request: Request, response: Response):
    """
    Authenticate and sync user with verified Firebase Authentication ID token.
    Never trusts client-supplied email, uid, or role.
    """
    client_ip = security_firewall._extract_client_ip(request)
    print(f"[Auth Info] POST /api/v1/auth/firebase-login received from {client_ip}", flush=True)
    
    # 1. Cryptographically verify the Firebase ID Token
    if not auth_data.id_token:
        print("[Auth Error] Firebase ID token was empty in request body", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token is required."
        )

    claims = verify_firebase_id_token(auth_data.id_token)
    if not claims:
        print("[Auth Error] verify_firebase_id_token returned None", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, forged, or expired Firebase ID token."
        )

    # 2. Extract verified identity claims
    verified_email = claims.get("email")
    if not verified_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verified Firebase token does not contain a valid email."
        )
    normalized_email = verified_email.strip().lower()
    verified_uid = claims.get("sub") or claims.get("user_id")
    verified_name = claims.get("name") or normalized_email.split("@")[0].capitalize()
    verified_photo = claims.get("picture", "")
    provider = "firebase"
    if isinstance(claims.get("firebase"), dict):
        provider = claims.get("firebase", {}).get("sign_in_provider", "firebase")

    # WAF Inspection on verified payload
    is_safe, threat_type, threat_msg, _ = await security_firewall.inspect_payload(
        request, {"email": normalized_email, "provider": provider}, endpoint_name="/api/v1/auth/firebase-login"
    )
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"[Security Firewall Blocked] {threat_msg}"
        )

    db = get_db()
    user = await db["users"].find_one({"email": normalized_email})
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if not user:
        user_id = verified_uid or f"usr_fb_{uuid.uuid4().hex[:8]}"
        default_brand_id = f"brand_{uuid.uuid4().hex[:8]}"
        
        # New users always receive "brand_manager" role (server-enforced)
        user_doc = {
            "id": user_id,
            "email": normalized_email,
            "full_name": verified_name,
            "role": "owner",
            "organization": auth_data.organization or "Local Business",
            "photo_url": verified_photo,
            "firebase_uid": verified_uid,
            "auth_provider": provider,
            "is_active": True,
            "created_at": now.isoformat(),
            "brand_ids": [default_brand_id],
            "login_count": 1,
            "last_login": now.isoformat()
        }
        await db["users"].insert_one(user_doc)
        
        # Provision default primary brand
        org_name = auth_data.organization or (verified_name + "'s Business" if verified_name else "My Business")
        clean_tag = ''.join(c for c in org_name if c.isalnum()) or "MyBusiness"
        brand_doc = {
            "id": default_brand_id,
            "owner_id": user_id,
            "name": f"{org_name}",
            "business_type": "retail",
            "industry": "Local Business",
            "description": f"Business workspace for {verified_name}.",
            "locations": [
                {
                    "id": f"loc_{uuid.uuid4().hex[:6]}",
                    "name": "Main Branch",
                    "address": "",
                    "city": "",
                    "phone": "",
                    "google_place_id": "",
                    "is_primary": True
                }
            ],
            "topics": ["Product Quality", "Price & Discounts", "Staff Behavior", "Store Cleanliness", "Stock Availability", "Billing Speed"],
            "products": [],
            "keywords": [org_name],
            "hashtags": [f"#{clean_tag}"],
            "social_handles": {},
            "competitors": [],
            "crisis_threshold_negative": 0.35,
            "is_primary": True,
            "created_at": now
        }
        await db["brands"].insert_one(brand_doc)
        user = user_doc
    else:
        update_fields = {
            "last_login": now.isoformat()
        }
        if verified_photo:
            update_fields["photo_url"] = verified_photo
        if verified_uid and not user.get("firebase_uid"):
            update_fields["firebase_uid"] = verified_uid
        if verified_name and (not user.get("full_name") or user.get("full_name") == "User"):
            update_fields["full_name"] = verified_name

        await db["users"].update_one(
            {"id": user["id"]},
            {"$set": update_fields, "$inc": {"login_count": 1}}
        )
        user.update(update_fields)

    security_firewall.record_successful_auth(client_ip)
    await record_auth_event(db, user, request, method=f"firebase_{provider}")

    access_token = create_access_token(subject=user["id"], role=user.get("role", "owner"))
    refresh_token = create_refresh_token(subject=user["id"])
    set_refresh_token_cookie(response, refresh_token, request)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**clean_doc(user)),
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response):
    """
    Issues a refreshed access token using the httpOnly refresh_token cookie
    or fallback X-Refresh-Token header / body.
    """
    token = request.cookies.get("refresh_token") or request.headers.get("x-refresh-token")
    if not token:
        try:
            body = await request.json()
            token = body.get("refresh_token")
        except Exception:
            pass

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_refresh_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    db = get_db()
    user = await db["users"].find_one({"id": user_id})
    if not user or not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    new_access_token = create_access_token(subject=user["id"], role=user.get("role", "owner"))
    new_refresh_token = create_refresh_token(subject=user["id"])
    set_refresh_token_cookie(response, new_refresh_token, request)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user": UserResponse(**clean_doc(user)),
        "refresh_token": new_refresh_token
    }

@router.post("/logout")
async def logout(response: Response):
    """
    Clears the httpOnly refresh token cookie to log out.
    """
    response.delete_cookie(key="refresh_token", path="/")
    return {"status": "success", "message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**clean_doc(current_user))

@router.get("/audit-logs", response_model=List[AuthLogResponse])
async def list_auth_audit_logs(
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch login authentication audit records stored in MongoDB 'auth_logs' collection.
    Admins see all logs; other users see only their own.
    """
    db = get_db()
    query = {} if current_user.get("role") == "admin" else {"user_id": current_user["id"]}
    cursor = db["auth_logs"].find(query).sort("login_timestamp", -1).limit(limit)
    logs = await cursor.to_list(limit)
    return clean_docs(logs)

@router.get("/firewall-status")
async def get_firewall_status(
    request: Request,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Returns real-time WAF firewall status, active rules, and threat statistics.
    Requires authentication.
    """
    client_ip = security_firewall._extract_client_ip(request)
    return security_firewall.get_status(client_ip)

@router.get("/firewall-logs")
async def get_firewall_logs(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin"))
):
    """
    Returns security violation and firewall block logs from MongoDB 'firewall_logs' collection.
    Restricted to admins.
    """
    db = get_db()
    cursor = db["firewall_logs"].find({}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(limit)
    return clean_docs(logs)

@router.post("/firewall-test")
async def test_firewall_defense(
    payload: dict,
    request: Request,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Interactive endpoint allowing developers and evaluators to test firewall defense in real time.
    Restricted to admins.
    """
    is_safe, threat_type, details, threat_score = await security_firewall.inspect_payload(
        request, payload, endpoint_name="/api/v1/auth/firewall-test"
    )
    return {
        "passed": is_safe,
        "threat_detected": not is_safe,
        "threat_type": threat_type,
        "details": details,
        "threat_score": threat_score,
        "action": "ALLOWED" if is_safe else "BLOCKED_BY_FIREWALL"
    }
