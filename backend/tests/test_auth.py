import pytest
import jwt
from unittest.mock import patch
from app.core.config import settings
from app.core.security import verify_old_pbkdf2, is_old_hash, create_access_token

@pytest.mark.asyncio
async def test_forged_or_unsigned_firebase_token_rejected(client):
    """
    Test 1: Forged or unsigned Firebase token is rejected with 401.
    """
    # 1. Unsigned token (none algorithm or fake signature)
    unsigned_token = jwt.encode({"sub": "attacker_uid", "email": "attacker@evil.com"}, key="", algorithm="none")
    res1 = await client.post("/api/v1/auth/firebase-login", json={"id_token": unsigned_token})
    assert res1.status_code == 401

    # 2. Forged HS256 token signed with random secret
    forged_token = jwt.encode({"sub": "attacker_uid", "email": "attacker@evil.com"}, key="random-secret", algorithm="HS256")
    res2 = await client.post("/api/v1/auth/firebase-login", json={"id_token": forged_token})
    assert res2.status_code == 401

    # 3. Completely bogus string
    res3 = await client.post("/api/v1/auth/firebase-login", json={"id_token": "totally-bogus-token"})
    assert res3.status_code == 401

@pytest.mark.asyncio
async def test_client_supplied_role_is_ignored(client, test_db):
    """
    Test 2: Client-supplied role is ignored in registration and firebase-login; new users get owner.
    """
    # Attempt to register with role="admin"
    register_payload = {
        "email": "hacker@brandpulse.ai",
        "full_name": "Privilege Escalation Attempt",
        "password": "Password123!",
        "role": "admin"
    }
    res = await client.post("/api/v1/auth/register", json=register_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "owner"

    # Verify directly in MongoDB
    user_in_db = await test_db["users"].find_one({"email": "hacker@brandpulse.ai"})
    assert user_in_db is not None
    assert user_in_db["role"] == "owner"

    # Also test Firebase login: client sends role in mock verified claims or payload
    mock_claims = {
        "sub": "firebase_uid_123",
        "email": "firebase_user@brandpulse.ai",
        "name": "Firebase User",
        "picture": "https://example.com/pic.jpg",
        "firebase": {"sign_in_provider": "google.com"}
    }
    with patch("app.api.v1.endpoints.auth.verify_firebase_id_token", return_value=mock_claims):
        fb_res = await client.post("/api/v1/auth/firebase-login", json={
            "id_token": "valid.mock.token",
            "role": "admin"
        })
        assert fb_res.status_code == 200
        fb_data = fb_res.json()
        assert fb_data["user"]["role"] == "owner"

@pytest.mark.asyncio
async def test_unknown_user_token_returns_401(client):
    """
    Test 3: Token referencing non-existent user returns 401.
    """
    ghost_token = create_access_token(subject="user_does_not_exist_in_db", role="owner")
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert res.status_code == 401
    assert "User not found or account is deactivated" in res.json().get("detail", "")

@pytest.mark.asyncio
async def test_admin_only_endpoints_return_403_for_non_admins(client, user_factory):
    """
    Test 4: Admin-only endpoints return 403 for non-admins (e.g. owner or staff).
    """
    # Create standard owner user
    _, bm_token = await user_factory(email="manager@brandpulse.ai", role="owner", user_id="usr_bm_01")
    
    # Firewall status endpoint (admin only)
    res_fw_status = await client.get("/api/v1/auth/firewall-status", headers={"Authorization": f"Bearer {bm_token}"})
    assert res_fw_status.status_code == 403
    assert "Required role: 'admin'" in res_fw_status.json().get("detail", "")

    # Firewall logs endpoint (admin only)
    res_fw = await client.get("/api/v1/auth/firewall-logs", headers={"Authorization": f"Bearer {bm_token}"})
    assert res_fw.status_code == 403
    assert "Required role: 'admin'" in res_fw.json().get("detail", "")

    # ML train endpoint (admin only)
    res_train = await client.post("/api/v1/ml/train", headers={"Authorization": f"Bearer {bm_token}"})
    assert res_train.status_code == 403

    # System db-status endpoint (admin only)
    res_sys = await client.get("/api/v1/system/db-status", headers={"Authorization": f"Bearer {bm_token}"})
    assert res_sys.status_code == 403

    # Now create an admin user
    _, admin_token = await user_factory(email="admin@brandpulse.ai", role="admin", user_id="usr_adm_01")
    
    res_admin_fw = await client.get("/api/v1/auth/firewall-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_fw.status_code == 200

    res_admin_sys = await client.get("/api/v1/system/db-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_sys.status_code == 200

@pytest.mark.asyncio
async def test_old_hash_login_upgrades_to_new_hash(client, test_db):
    """
    Test 5: Old PBKDF2 hash verifies successfully on login and is upgraded to bcrypt hash.
    """
    import hashlib
    # Compute legacy PBKDF2 hash using settings.SECRET_KEY
    legacy_password = "LegacyPassword123!"
    salt = settings.SECRET_KEY[:16].encode("utf-8")
    old_hash = hashlib.pbkdf2_hmac("sha256", legacy_password.encode("utf-8"), salt, 100000).hex()
    
    # Assert it matches old hash signature
    assert is_old_hash(old_hash) is True

    user_id = "usr_legacy_migration"
    email = "legacy_user@brandpulse.ai"
    await test_db["users"].delete_one({"email": email})
    await test_db["users"].insert_one({
        "id": user_id,
        "email": email,
        "full_name": "Legacy User",
        "role": "owner",
        "hashed_password": old_hash,
        "is_active": True,
        "brand_ids": ["test_brand_01"],
        "created_at": "2026-01-01T00:00:00"
    })

    # Login with the legacy password
    login_res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": legacy_password
    })
    assert login_res.status_code == 200

    # Verify that the database record has been upgraded to bcrypt
    updated_user = await test_db["users"].find_one({"id": user_id})
    new_hash = updated_user.get("hashed_password")
    assert is_old_hash(new_hash) is False
    assert new_hash.startswith(("$2a$", "$2b$", "$2y$"))

@pytest.mark.asyncio
async def test_demo_login_disabled_when_demo_mode_false(client):
    """
    Test 6: Demo login is disabled when DEMO_MODE is false.
    """
    with patch.object(settings, "DEMO_MODE", False):
        res = await client.post("/api/v1/auth/demo-login")
        assert res.status_code == 403
        assert "Demo login is disabled" in res.json().get("detail", "")

@pytest.mark.asyncio
async def test_demo_login_succeeds_when_demo_mode_true_for_fixed_owner(client):
    """
    Demo login logs in as fixed demo owner account when DEMO_MODE=true.
    """
    with patch.object(settings, "DEMO_MODE", True):
        res = await client.post("/api/v1/auth/demo-login")
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["role"] == "owner"
        assert data["user"]["email"] == "demo_owner@brandpulse.ai"
        assert "access_token" in data

@pytest.mark.asyncio
async def test_email_normalization(client, test_db):
    """
    Registers with mixed case and spaces, then verifies lookup is lowercase and normalized.
    """
    email_mixed = "   MixedCase.User@BrandPulse.AI  "
    res = await client.post("/api/v1/auth/register", json={
        "email": email_mixed,
        "full_name": "Mixed Case",
        "password": "Password123!"
    })
    assert res.status_code == 200
    expected_email = "mixedcase.user@brandpulse.ai"
    assert res.json()["user"]["email"] == expected_email

    # Duplicate registration with different casing should fail with 400
    res_dup = await client.post("/api/v1/auth/register", json={
        "email": "MIXEDCASE.USER@BRANDPULSE.AI",
        "full_name": "Duplicate Attempt",
        "password": "Password123!"
    })
    assert res_dup.status_code == 400

@pytest.mark.asyncio
async def test_refresh_token_cookie_flow(client, user_factory):
    """
    Tests that login sets httpOnly refresh_token cookie, /auth/refresh returns new access token,
    and /auth/logout clears the cookie.
    """
    email = "refreshtest@brandpulse.ai"
    password = "SecurePassword123!"
    await user_factory(email=email, password=password, user_id="usr_refresh_01")

    # 1. Login
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    assert "refresh_token" in login_res.cookies

    # 2. Call /auth/refresh with the cookie present in client session
    refresh_res = await client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    refreshed_data = refresh_res.json()
    assert "access_token" in refreshed_data

    # 3. Call /auth/logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

def test_secret_key_validation_raises_when_short_or_missing():
    """
    Test 7: SECRET_KEY shorter than 32 chars or missing raises at startup.
    """
    import os
    import sys
    import subprocess
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = """
import os
os.environ['SECRET_KEY'] = 'short-key'
import importlib
import app.core.config
importlib.reload(app.core.config)
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = backend_dir
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=backend_dir)
    assert result.returncode != 0
    assert "SECRET_KEY environment variable is required and must be at least 32 characters long" in result.stderr

