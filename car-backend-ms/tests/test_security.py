from unittest.mock import patch

import pytest
from firebase_admin.exceptions import FirebaseError

from app.core.security import verify_firebase_token


class TestVerifyFirebaseToken:
    def test_returns_decoded_claims_on_valid_token(self):
        fake_claims = {"uid": "uid123", "email": "user@example.com", "name": "User"}
        with patch("app.core.security._get_app"), \
             patch("app.core.security.auth.verify_id_token", return_value=fake_claims):
            result = verify_firebase_token("valid-token")
        assert result == fake_claims

    def test_passes_token_to_firebase(self):
        fake_claims = {"uid": "uid123"}
        with patch("app.core.security._get_app"), \
             patch("app.core.security.auth.verify_id_token", return_value=fake_claims) as mock_verify:
            verify_firebase_token("my-id-token")
        mock_verify.assert_called_once_with("my-id-token")

    def test_propagates_firebase_error_on_invalid_token(self):
        with patch("app.core.security._get_app"), \
             patch("app.core.security.auth.verify_id_token",
                   side_effect=FirebaseError("invalid-argument", "bad token")):
            with pytest.raises(FirebaseError):
                verify_firebase_token("bad-token")
