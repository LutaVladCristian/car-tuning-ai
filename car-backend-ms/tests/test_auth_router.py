from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.models.user import User
from dependencies import get_db
from main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_register_creates_user_and_rejects_duplicates():
    client = TestClient(app)

    payload = {
        "username": "driver",
        "email": "driver@example.com",
        "password": "super-secret",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == payload["username"]
    assert body["email"] == payload["email"]
    assert "id" in body
    assert "hashed_password" not in body

    duplicate = client.post("/auth/register", json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Username already taken"


def test_login_returns_bearer_token_for_valid_credentials():
    client = TestClient(app)
    client.post(
        "/auth/register",
        json={
            "username": "driver",
            "email": "driver@example.com",
            "password": "super-secret",
        },
    )

    response = client.post(
        "/auth/login",
        json={"username": "driver", "password": "super-secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_invalid_password():
    client = TestClient(app)
    db = TestingSessionLocal()
    db.add(
        User(
            username="driver",
            email="driver@example.com",
            hashed_password=hash_password("super-secret"),
        )
    )
    db.commit()
    db.close()

    response = client.post(
        "/auth/login",
        json={"username": "driver", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
