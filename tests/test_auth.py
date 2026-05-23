"""Unit tests for JWT authentication and RBAC."""

import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt
from fastapi import HTTPException

from app.config import settings
from app.auth import create_access_token, decode_token


class TestTokenCreation:
    """Tests for JWT token creation."""

    def test_create_token_with_valid_data(self):
        """Token is created successfully with valid data."""
        token = create_access_token(data={"sub": "testuser", "role": "analyst"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_correct_claims(self):
        """Token payload contains the expected claims."""
        token = create_access_token(data={"sub": "admin_user", "role": "admin"})
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["sub"] == "admin_user"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_with_custom_expiry(self):
        """Token respects custom expiration delta."""
        token = create_access_token(
            data={"sub": "user", "role": "analyst"},
            expires_delta=timedelta(minutes=5),
        )
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        diff = (exp - iat).total_seconds()
        assert 290 <= diff <= 310  # ~5 minutes with tolerance


class TestTokenDecoding:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_token(self):
        """Valid token decodes successfully."""
        token = create_access_token(data={"sub": "testuser", "role": "analyst"})
        payload = decode_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "analyst"

    def test_decode_invalid_token_raises(self):
        """Invalid token raises HTTPException with 401."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.string")
        assert exc_info.value.status_code == 401

    def test_decode_expired_token_raises(self):
        """Expired token raises HTTPException with 401."""
        token = create_access_token(
            data={"sub": "user", "role": "analyst"},
            expires_delta=timedelta(seconds=-10),
        )
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_decode_wrong_secret_raises(self):
        """Token signed with wrong secret is rejected."""
        token = jwt.encode(
            {
                "sub": "user",
                "role": "admin",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "wrong_secret",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401


class TestRBAC:
    """Tests for role-based access control logic."""

    def test_analyst_role_in_token(self):
        """Analyst role is correctly encoded and decoded."""
        token = create_access_token(data={"sub": "analyst1", "role": "analyst"})
        payload = decode_token(token)
        assert payload["role"] == "analyst"

    def test_admin_role_in_token(self):
        """Admin role is correctly encoded and decoded."""
        token = create_access_token(data={"sub": "admin1", "role": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_token_without_role_is_invalid(self):
        """Token missing role claim should be rejected by get_current_user."""
        token = create_access_token(data={"sub": "user_no_role"})
        payload = decode_token(token)
        assert payload.get("role") is None
