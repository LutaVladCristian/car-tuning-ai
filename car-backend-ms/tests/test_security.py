import pytest
from jose import JWTError

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_password_round_trip():
    hashed = hash_password("super-secret")

    assert hashed != "super-secret"
    assert verify_password("super-secret", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_round_trip():
    token = create_access_token("driver")

    assert decode_access_token(token) == "driver"


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(JWTError):
        decode_access_token("not-a-jwt")
