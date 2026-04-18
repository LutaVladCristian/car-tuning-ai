import pytest
from pydantic import ValidationError

from app.schemas.auth import FirebaseAuthRequest, UserResponse


class TestFirebaseAuthRequest:
    def test_valid_token_accepted(self):
        req = FirebaseAuthRequest(id_token="firebase-id-token-value")
        assert req.id_token == "firebase-id-token-value"

    def test_missing_token_raises(self):
        with pytest.raises(ValidationError):
            FirebaseAuthRequest()


class TestUserResponse:
    def test_valid_response_accepted(self):
        resp = UserResponse(id=1, firebase_uid="uid123", email="user@example.com", display_name="User")
        assert resp.firebase_uid == "uid123"
        assert resp.email == "user@example.com"
        assert resp.display_name == "User"

    def test_display_name_can_be_none(self):
        resp = UserResponse(id=1, firebase_uid="uid123", email="user@example.com", display_name=None)
        assert resp.display_name is None

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            UserResponse(display_name="User")
