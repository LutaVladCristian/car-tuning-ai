import os
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FIREBASE_PROJECT_ID"] = "test-project"
os.environ["FIREBASE_STORAGE_BUCKET"] = "test-project.firebasestorage.app"
os.environ["SEGMENTATION_MS_URL"] = "http://fake-seg:8000"

import pytest
from fastapi.testclient import TestClient
from main import app as fastapi_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models.photo  # noqa: F401
import app.db.models.user  # noqa: F401
from app.db.base import Base
from app.db.models.photo import OperationType, Photo
from app.db.models.user import User
from dependencies import get_db

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Shared constants reused by individual test modules.
FAKE_UID = "test-firebase-uid"
FAKE_TOKEN = "fake-firebase-id-token"
FAKE_CLAIMS = {"uid": FAKE_UID, "email": "alice@example.com", "name": "Alice"}


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

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    try:
        # Patch the Firebase token verification so tests never hit Firebase.
        with patch("dependencies.verify_firebase_token", return_value=FAKE_CLAIMS):
            with TestClient(fastapi_app, raise_server_exceptions=True) as c:
                yield c
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    def _factory(firebase_uid=FAKE_UID, email="alice@example.com", display_name="Alice"):
        user = User(firebase_uid=firebase_uid, email=email, display_name=display_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _factory


@pytest.fixture()
def user_and_token(make_user):
    user = make_user()
    return user, FAKE_TOKEN


@pytest.fixture()
def auth_headers(user_and_token):
    _, token = user_and_token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_photo(db):
    def _factory(
        user,
        filename="car.jpg",
        operation_type=OperationType.edit_photo,
        original_image_path="gs://test-bucket/users/uid/photos/abc/original.png",
        result_image_path="gs://test-bucket/users/uid/photos/abc/result.png",
        operation_params=None,
    ):
        photo = Photo(
            user_id=user.id,
            original_filename=filename,
            original_image_path=original_image_path,
            result_image_path=result_image_path,
            operation_type=operation_type,
            operation_params=operation_params or {},
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        return photo

    return _factory
