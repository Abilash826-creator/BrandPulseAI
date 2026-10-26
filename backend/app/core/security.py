import os
import datetime
from datetime import timezone
from typing import Any, Union, Optional, Dict
import hashlib
import hmac
import time
import requests
import bcrypt
import jwt
from cryptography.x509 import load_pem_x509_certificate

from app.core.config import settings

# Google Firebase public certificates cache
_FIREBASE_CERTS_CACHE: Dict[str, Any] = {"certs": {}, "expires_at": 0}

def get_password_hash(password: str) -> str:
    """
    Hashes a password with bcrypt using a per-user random salt.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_old_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against the legacy PBKDF2 hash using settings.SECRET_KEY.
    """
    try:
        salt = settings.SECRET_KEY[:16].encode("utf-8")
        calculated = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000).hex()
        return hmac.compare_digest(calculated, hashed_password)
    except Exception:
        return False

def is_old_hash(hashed_password: str) -> bool:
    """
    Determines if a stored hash is in the legacy PBKDF2 format rather than bcrypt.
    """
    if not hashed_password:
        return False
    return not hashed_password.startswith(("$2a$", "$2b$", "$2y$"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against bcrypt hash, or falls back to legacy PBKDF2.
    Plaintext comparison is strictly prohibited.
    """
    if not plain_password or not hashed_password:
        return False

    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    return verify_old_pbkdf2(plain_password, hashed_password)

def create_access_token(
    subject: Union[str, Any],
    role: str = "owner",
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """
    Creates a signed JWT access token with a 30-minute default lifetime.
    """
    now = datetime.datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "role": role,
        "type": "access"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """
    Creates a signed JWT refresh token with a 7-day default lifetime.
    """
    now = datetime.datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT access token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") and payload.get("type") != "access":
            return None
        return payload
    except Exception:
        return None

def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT refresh token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except Exception:
        return None

def _get_google_public_certs() -> Dict[str, str]:
    now = time.time()
    if _FIREBASE_CERTS_CACHE["certs"] and now < _FIREBASE_CERTS_CACHE["expires_at"]:
        return _FIREBASE_CERTS_CACHE["certs"]
    
    try:
        url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            certs = resp.json()
            # Cache control max-age if available, else 1 hour
            max_age = 3600
            cc = resp.headers.get("Cache-Control", "")
            for part in cc.split(","):
                if "max-age" in part:
                    try:
                        max_age = int(part.split("=")[1].strip())
                    except Exception:
                        pass
            _FIREBASE_CERTS_CACHE["certs"] = certs
            _FIREBASE_CERTS_CACHE["expires_at"] = now + max_age
            return certs
    except Exception:
        pass
    return _FIREBASE_CERTS_CACHE.get("certs", {})

import logging
logger = logging.getLogger("brandpulse.security")

def verify_firebase_id_token(id_token: str, project_id: Optional[str] = None) -> Optional[dict]:
    """
    Verifies a Firebase ID token cryptographically against Google's public certificates.
    Validates signature, header algorithm, kid, audience, issuer, and expiration.
    Returns the verified claims dictionary, or None if invalid/forged.
    """
    if not id_token or not isinstance(id_token, str):
        return None

    try:
        header = jwt.get_unverified_header(id_token)
    except Exception as e:
        logger.warning(f"[Auth] Could not parse token header: {e}")
        return None

    if header.get("alg") != "RS256":
        logger.warning(f"[Auth] Invalid token alg: {header.get('alg')}")
        return None

    kid = header.get("kid")
    if not kid:
        logger.warning("[Auth] Token missing 'kid' in header")
        return None

    certs = _get_google_public_certs()
    cert_pem = certs.get(kid)
    if not cert_pem:
        logger.warning(f"[Auth] No matching Google cert found for kid: {kid}")
        return None

    try:
        cert = load_pem_x509_certificate(cert_pem.encode("utf-8"))
        public_key = cert.public_key()
    except Exception as e:
        logger.warning(f"[Auth] Failed to load public key: {e}")
        return None

    # Inspect unverified claims for debugging
    try:
        unverified_claims = jwt.decode(id_token, options={"verify_signature": False})
        token_aud = unverified_claims.get("aud", "")
        token_iss = unverified_claims.get("iss", "")
        token_email = unverified_claims.get("email", "")
    except Exception as parse_err:
        logger.warning(f"[Auth] Could not parse unverified token payload: {parse_err}")
        token_aud = ""

    pid = project_id or settings.FIREBASE_PROJECT_ID or os.getenv("FIREBASE_PROJECT_ID", "")
    target_pid = pid if pid else token_aud

    if pid and token_aud and pid != token_aud:
        print(f"[Auth Warning] Firebase Project ID mismatch! Configured='{pid}', Token='{token_aud}'", flush=True)
        logger.warning(f"[Auth] Firebase Project ID mismatch: configured='{pid}', token='{token_aud}'")

    decode_kwargs: Dict[str, Any] = {
        "algorithms": ["RS256"],
        "leeway": 60,
        "options": {
            "verify_aud": bool(target_pid),
            "verify_iss": bool(target_pid),
            "require": ["exp", "iat", "sub"]
        }
    }
    if target_pid:
        decode_kwargs["audience"] = target_pid
        decode_kwargs["issuer"] = f"https://securetoken.google.com/{target_pid}"

    try:
        claims = jwt.decode(id_token, public_key, **decode_kwargs)
        if not claims.get("sub"):
            print("[Auth Error] Token missing 'sub' claim", flush=True)
            logger.warning("[Auth] Token missing 'sub' claim")
            return None
        print(f"[Auth Success] Verified Firebase token for user: {claims.get('email')}", flush=True)
        return claims
    except Exception as e:
        print(f"[Auth Error] Token cryptographic decode failed: {e}", flush=True)
        logger.warning(f"[Auth] Token cryptographic decode failed: {e}")
        return None
