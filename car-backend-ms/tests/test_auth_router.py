from unittest.mock import patch

from firebase_admin.exceptions import FirebaseError

_FAKE_UID = "test-firebase-uid"
_FAKE_TOKEN = "fake-firebase-id-token"
_FAKE_CLAIMS = {"uid": _FAKE_UID, "email": "alice@example.com", "name": "Alice"}


class TestHealthCheck:
    def test_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestFirebaseAuth:
    def test_valid_token_creates_user_and_returns_200(self, client):
        with patch("app.routers.auth.verify_firebase_token", return_value=_FAKE_CLAIMS):
            resp = client.post("/auth/firebase", json={"id_token": _FAKE_TOKEN})
        assert resp.status_code == 200
        body = resp.json()
        assert body["firebase_uid"] == _FAKE_UID
        assert body["email"] == "alice@example.com"
        assert body["display_name"] == "Alice"
        assert "id" in body

    def test_calling_twice_updates_existing_user(self, client, make_user):
        user = make_user()
        updated_claims = {**_FAKE_CLAIMS, "email": "new@example.com", "name": "New Name"}
        with patch("app.routers.auth.verify_firebase_token", return_value=updated_claims):
            resp = client.post("/auth/firebase", json={"id_token": _FAKE_TOKEN})
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == user.id
        assert body["email"] == "new@example.com"
        assert body["display_name"] == "New Name"

    def test_invalid_token_returns_401(self, client):
        with patch(
            "app.routers.auth.verify_firebase_token",
            side_effect=FirebaseError("invalid-argument", "bad token"),
        ):
            resp = client.post("/auth/firebase", json={"id_token": "bad-token"})
        assert resp.status_code == 401

    def test_missing_id_token_returns_422(self, client):
        resp = client.post("/auth/firebase", json={})
        assert resp.status_code == 422
