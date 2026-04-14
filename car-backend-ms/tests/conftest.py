import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["SEGMENTATION_MS_URL"] = "http://fake-seg:8000"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models.photo  # noqa: F401
import app.db.models.user  # noqa: F401
from app.db.base import Base
from app.db.models.photo import OperationType, Photo
from app.db.models.user import User
from app.core.security import create_access_token, hash_password
from dependencies import get_db
from main import app

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True)
def _reset_schema():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db(_reset_schema):
    session = _TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    def _factory(username="alice", email="alice@example.com", password="password123"):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _factory


@pytest.fixture()
def user_and_token(make_user):
    user = make_user()
    token = create_access_token(user.username)
    return user, token


@pytest.fixture()
def auth_headers(user_and_token):
    _, token = user_and_token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_photo(db):
    def _factory(
        user,
        filename="car.jpg",
        operation_type=OperationType.car_segmentation,
        original_image=b"original",
        result_image=b"result",
        operation_params=None,
    ):
        photo = Photo(
            user_id=user.id,
            original_filename=filename,
            original_image=original_image,
            result_image=result_image,
            operation_type=operation_type,
            operation_params=operation_params or {},
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        return photo

    return _factory
