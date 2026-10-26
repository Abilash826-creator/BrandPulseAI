import os
import sys
import pytest
import pytest_asyncio
import httpx
from unittest.mock import AsyncMock, patch

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure valid test environment settings before importing settings/app
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-chars-long-for-tests-12345"
os.environ["DEMO_MODE"] = "true"

import mongomock_motor
from main import app
from app.core.config import settings
from app.core.database import db_manager, get_db
from app.core.security import get_password_hash, create_access_token

@pytest_asyncio.fixture
async def test_db():
    """
    Provides an isolated in-memory MongoDB database using mongomock-motor.
    """
    client = mongomock_motor.AsyncMongoMockClient()
    db = client["test_brandpulse_ai"]
    return db

@pytest_asyncio.fixture
async def client(test_db):
    """
    Provides an httpx.AsyncClient connected to the FastAPI application via ASGITransport,
    with get_db overridden to use test_db and MongoDB startup mocked.
    """
    # Override database dependency and internal state
    app.dependency_overrides[get_db] = lambda: test_db
    original_db = db_manager.db
    original_conn = db_manager.is_mongodb_connected
    db_manager.db = test_db
    db_manager.is_mongodb_connected = True

    # Mock db_manager.connect and db_manager.close to avoid live network calls during lifespan
    with patch.object(db_manager, "connect", AsyncMock(return_value=(True, "Mock connected"))), \
         patch.object(db_manager, "close", AsyncMock(return_value=None)):
        
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="https://test") as ac:
            yield ac

    # Clean up overrides
    app.dependency_overrides.pop(get_db, None)
    db_manager.db = original_db
    db_manager.is_mongodb_connected = original_conn

class UserFixtureResult(tuple):
    def __new__(cls, user_doc, token):
        user_doc["access_token"] = token
        return super().__new__(cls, (user_doc, token))

    def __getitem__(self, item):
        if isinstance(item, str):
            if item == "access_token":
                return self[1]
            return self[0][item]
        return super().__getitem__(item)

    def get(self, key, default=None):
        if key == "access_token":
            return self[1]
        return self[0].get(key, default)

@pytest.fixture
def user_factory(test_db):
    """
    Helper fixture to create a user in the test database with a given role,
    password, and active status, and return the user document and their JWT access token.
    Supports both tuple unpacking: (user, token) and dict access: user['access_token'].
    """
    async def _create_user(
        email: str = "user@brandpulse.ai",
        role: str = "owner",
        password: str = "SecurePass123!",
        is_active: bool = True,
        user_id: str = "test_user_01"
    ):
        hashed_password = get_password_hash(password)
        user_doc = {
            "id": user_id,
            "email": email.strip().lower(),
            "full_name": "Test User",
            "role": role,
            "organization": "Test Organization",
            "hashed_password": hashed_password,
            "is_active": is_active,
            "brand_ids": ["test_brand_01"],
            "created_at": "2026-01-01T00:00:00"
        }
        await test_db["users"].delete_one({"email": email.strip().lower()})
        await test_db["users"].insert_one(user_doc)

        token = create_access_token(subject=user_id, role=role)
        return UserFixtureResult(user_doc, token)

    return _create_user
