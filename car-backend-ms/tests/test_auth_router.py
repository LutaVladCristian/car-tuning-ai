class TestHealthCheck:
    def test_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestRegister:
    def test_success_returns_201_with_user_fields(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "password1"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["username"] == "bob"
        assert body["email"] == "bob@example.com"
        assert "id" in body
        assert "created_at" in body
        assert "password" not in body
        assert "hashed_password" not in body

    def test_duplicate_username_returns_409(self, client, make_user):
        make_user(username="alice")
        resp = client.post(
            "/auth/register",
            json={"username": "alice", "email": "other@example.com", "password": "password1"},
        )
        assert resp.status_code == 409
        assert "Username already taken" in resp.json()["detail"]

    def test_duplicate_email_returns_409(self, client, make_user):
        make_user(email="shared@example.com")
        resp = client.post(
            "/auth/register",
            json={"username": "newuser", "email": "shared@example.com", "password": "password1"},
        )
        assert resp.status_code == 409
        assert "Email already registered" in resp.json()["detail"]

    def test_short_password_returns_422(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "bob", "email": "not-an-email", "password": "password1"},
        )
        assert resp.status_code == 422

    def test_short_username_returns_422(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "ab", "email": "bob@example.com", "password": "password1"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_valid_credentials_return_200_with_token(self, client, make_user):
        make_user(username="alice", password="password123")
        resp = client.post(
            "/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 0

    def test_wrong_password_returns_401(self, client, make_user):
        make_user(username="alice", password="correct")
        resp = client.post(
            "/auth/login",
            json={"username": "alice", "password": "wrong"},
        )
        assert resp.status_code == 401
        assert "Invalid username or password" in resp.json()["detail"]

    def test_unknown_username_returns_401(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "nobody", "password": "password123"},
        )
        assert resp.status_code == 401

    def test_returned_token_is_decodable(self, client, make_user):
        make_user(username="alice", password="password123")
        resp = client.post(
            "/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        token = resp.json()["access_token"]

        from app.core.security import decode_access_token
        assert decode_access_token(token) == "alice"
