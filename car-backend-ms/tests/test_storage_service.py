from unittest.mock import MagicMock, patch

import pytest

from app.services.storage_service import upload_photo


def test_upload_photo_rejects_unknown_role():
    with pytest.raises(ValueError, match="Unsupported photo role"):
        upload_photo("uid", "thumbnail", b"png")


def test_upload_photo_sets_owner_metadata():
    bucket = MagicMock()
    blob = MagicMock()
    bucket.blob.return_value = blob

    with patch("app.services.storage_service._get_app"), patch(
        "app.services.storage_service.storage.bucket", return_value=bucket
    ):
        path = upload_photo("uid-123", "mask", b"png")

    assert path.startswith("users/uid-123/photos/")
    assert path.endswith("/mask.png")
    assert blob.metadata == {"firebase_uid": "uid-123", "role": "mask"}
    blob.upload_from_string.assert_called_once_with(b"png", content_type="image/png")
