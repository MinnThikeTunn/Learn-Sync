import asyncio
import time
import uuid
import jwt
import pytest
from fastapi import HTTPException
from uuid import UUID

from backend.app.core.config import settings
from backend.app.core.auth import get_current_user


def create_test_jwt(user_id: UUID, secret: str = "super-secret-jwt-key", expires_in: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "aud": "authenticated",
        "role": "authenticated",
        "email": "student@learnsync.ai",
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_get_current_user_with_valid_jwt(monkeypatch):
    user_id = uuid.uuid4()
    secret = "test-supabase-jwt-secret-12345"
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    token = create_test_jwt(user_id, secret=secret, expires_in=3600)
    auth_header = f"Bearer {token}"

    authenticated_id = asyncio.run(get_current_user(authorization=auth_header, x_test_user_id=None))
    assert authenticated_id == user_id


def test_get_current_user_with_expired_jwt(monkeypatch):
    user_id = uuid.uuid4()
    secret = "test-supabase-jwt-secret-12345"
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    # Expired token (-60s)
    token = create_test_jwt(user_id, secret=secret, expires_in=-60)
    auth_header = f"Bearer {token}"

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(authorization=auth_header, x_test_user_id=None))
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower() or "invalid" in exc_info.value.detail.lower()


def test_get_current_user_missing_credentials(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(authorization=None, x_test_user_id=None))
    assert exc_info.value.status_code == 401


def test_get_current_user_invalid_token(monkeypatch):
    secret = "test-supabase-jwt-secret-12345"
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(authorization="Bearer completely-invalid-jwt-token", x_test_user_id=None))
    assert exc_info.value.status_code == 401


def test_get_current_user_dev_test_header_in_dev(monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    authenticated_id = asyncio.run(get_current_user(authorization=None, x_test_user_id=str(user_id)))
    assert authenticated_id == user_id


def test_get_current_user_dev_test_header_disabled_in_prod(monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(authorization=None, x_test_user_id=str(user_id)))
    assert exc_info.value.status_code == 401
