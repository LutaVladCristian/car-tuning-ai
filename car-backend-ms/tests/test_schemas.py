import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, TokenResponse


class TestRegisterRequest:
    def test_valid_payload_accepted(self):
        req = RegisterRequest(username="alice", email="alice@example.com", password="secret99")
        assert req.username == "alice"
        assert req.email == "alice@example.com"

    def test_username_too_short_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="ab", email="a@b.com", password="secret99")

    def test_username_too_long_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="a" * 51, email="a@b.com", password="secret99")

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="alice", email="not-an-email", password="secret99")

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="alice", email="a@b.com", password="short")

    def test_password_exactly_8_chars_accepted(self):
        req = RegisterRequest(username="alice", email="a@b.com", password="exact123")
        assert len(req.password) == 8

    def test_username_exactly_3_chars_accepted(self):
        req = RegisterRequest(username="abc", email="a@b.com", password="secret99")
        assert req.username == "abc"

    def test_username_exactly_50_chars_accepted(self):
        req = RegisterRequest(username="a" * 50, email="a@b.com", password="secret99")
        assert len(req.username) == 50


class TestTokenResponse:
    def test_default_token_type_is_bearer(self):
        resp = TokenResponse(access_token="sometoken")
        assert resp.token_type == "bearer"

    def test_custom_token_type_accepted(self):
        resp = TokenResponse(access_token="sometoken", token_type="custom")
        assert resp.token_type == "custom"
