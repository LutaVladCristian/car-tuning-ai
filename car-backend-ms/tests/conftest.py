import os
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ["FIREBASE_PROJECT_ID"] = "test-project"
os.environ["FIREBASE_STORAGE_BUCKET"] = "test-project.firebasestorage.app"
os.environ["SEGMENTATION_MS_URL"] = "http://fake-seg:8000"

from main import app as fastapi_app

from app.domain import OperationType, PhotoRecord, PhotoStatus, UserRecord
from app.services.photo_store import InMemoryPhotoStore
from dependencies import get_store

# Shared constants reused by individual test modules.
FAKE_UID = "test-firebase-uid"
FAKE_TOKEN = "fake-firebase-id-token"
FAKE_CLAIMS = {"uid": FAKE_UID, "email": "alice@example.com", "name": "Alice"}


@pytest.fixture()
def store():
    return InMemoryPhotoStore()


@pytest.fixture()
def client(store):
    def _override_get_store():
        return store

    fastapi_app.dependency_overrides[get_store] = _override_get_store
    try:
        with patch("dependencies.verify_firebase_token", return_value=FAKE_CLAIMS):
            with TestClient(fastapi_app, raise_server_exceptions=True) as c:
                yield c
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def make_user(store):
    def _factory(firebase_uid=FAKE_UID, email="alice@example.com", display_name="Alice"):
        return store.sync_user(firebase_uid, email, display_name)

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
def make_photo(store):
    def _factory(
        user: UserRecord,
        filename="car.jpg",
        operation_type=OperationType.edit_photo,
        original_image_path="gs://test-bucket/users/uid/photos/abc/original.png",
        prepared_image_path=None,
        result_image_path="gs://test-bucket/users/uid/photos/abc/result.png",
        raw_mask_image_path=None,
        mask_image_path=None,
        status=PhotoStatus.completed,
        operation_params=None,
    ):
        prepared_path = (
            "gs://test-bucket/users/uid/photos/abc/prepared.png"
            if prepared_image_path is None
            else prepared_image_path
        )
        raw_mask_path = (
            "gs://test-bucket/users/uid/photos/abc/raw-mask.png"
            if raw_mask_image_path is None and status is not PhotoStatus.completed
            else raw_mask_image_path
        )
        mask_path = (
            "gs://test-bucket/users/uid/photos/abc/mask.png"
            if mask_image_path is None and status is not PhotoStatus.completed
            else mask_image_path
        )
        created = store.create_preview_photo(
            user,
            original_filename=filename,
            original_image_path=original_image_path,
            prepared_image_path=prepared_path,
            raw_mask_image_path=raw_mask_path,
            mask_image_path=mask_path,
            operation_params=operation_params or {},
        )
        photo = PhotoRecord(
            id=created.id,
            user_id=user.id,
            original_filename=created.original_filename,
            original_image_path=created.original_image_path,
            prepared_image_path=created.prepared_image_path,
            result_image_path=result_image_path,
            raw_mask_image_path=created.raw_mask_image_path,
            mask_image_path=created.mask_image_path,
            status=status,
            operation_type=operation_type,
            operation_params=operation_params or {},
            created_at=datetime.now(UTC),
        )
        store._photos[user.firebase_uid][photo.id] = photo
        return photo

    return _factory
