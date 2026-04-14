import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestHashPassword:
    def test_returns_a_string(self):
        result = hash_password("mysecret")
        assert isinstance(result, str)

    def test_hash_is_not_the_plain_text(self):
        plain = "mysecret"
        assert hash_password(plain) != plain

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses a random salt
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password_returns_false(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False


class TestCreateAndDecodeToken:
    def test_create_returns_a_string(self):
        token = create_access_token("alice")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_returns_original_subject(self):
        token = create_access_token("alice")
        assert decode_access_token(token) == "alice"

    def test_decode_invalid_token_raises_jwt_error(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.token")

    def test_decode_tampered_token_raises_jwt_error(self):
        token = create_access_token("alice")
        tampered = token[:-4] + "xxxx"
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_decode_token_without_sub_raises_jwt_error(self):
        from jose import jwt
        from app.core.security import JWT_SECRET_KEY
        # Create a token that has no "sub" claim
        raw = jwt.encode({"data": "nope"}, JWT_SECRET_KEY, algorithm="HS256")
        with pytest.raises(JWTError):
            decode_access_token(raw)
