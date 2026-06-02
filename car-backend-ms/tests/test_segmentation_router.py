from unittest.mock import AsyncMock, MagicMock, patch

from app.db.models.photo import Photo, PhotoStatus

FAKE_IMAGE = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
)
FAKE_PNG = b"\x89PNG_FAKE"


def _uploads():
    return patch("app.routers.segmentation.storage_service.upload_photo", MagicMock(side_effect=lambda uid, role, data: f"users/{uid}/{role}.png"))


def test_preview_persists_hidden_masks(client, auth_headers, db):
    with patch("app.routers.segmentation.proxy_service.forward_segment_photo", AsyncMock(return_value=(FAKE_PNG, FAKE_PNG, FAKE_PNG))), _uploads():
        response = client.post("/edit-photo/preview", files={"file": ("car.png", FAKE_IMAGE, "image/png")}, data={"prompt": "red", "edit_car": "true"}, headers=auth_headers)
    assert response.status_code == 200
    photo = db.query(Photo).one()
    assert photo.status == PhotoStatus.preview
    assert photo.prepared_image_path.endswith("/prepared.png")
    assert photo.raw_mask_image_path.endswith("/raw-mask.png")
    assert photo.mask_image_path.endswith("/mask.png")


def test_generate_completes_preview(client, auth_headers, user_and_token, db, make_photo):
    user, _ = user_and_token
    photo = make_photo(
        user,
        result_image_path=None,
        status=PhotoStatus.preview,
        operation_params={"prompt": "red", "size": "auto"},
    )
    photo.prepared_image_path = "prepared"
    photo.mask_image_path = "mask"
    db.commit()
    with patch("app.routers.segmentation.storage_service.download_photo", MagicMock(return_value=FAKE_PNG)), _uploads(), patch(
        "app.routers.segmentation.proxy_service.forward_generate_photo", AsyncMock(return_value=FAKE_PNG)
    ):
        response = client.post(f"/edit-photo/{photo.id}/generate", headers=auth_headers)
    assert response.status_code == 200
    db.refresh(photo)
    assert photo.status == PhotoStatus.completed


def test_generate_rejects_preview_missing_params(client, auth_headers, user_and_token, db, make_photo):
    user, _ = user_and_token
    photo = make_photo(user, result_image_path=None, status=PhotoStatus.preview)
    photo.prepared_image_path = "prepared"
    photo.mask_image_path = "mask"
    db.commit()
    response = client.post(f"/edit-photo/{photo.id}/generate", headers=auth_headers)
    assert response.status_code == 409
    db.refresh(photo)
    assert photo.status == PhotoStatus.preview


def test_delete_preview_removes_record(client, auth_headers, user_and_token, db, make_photo):
    user, _ = user_and_token
    photo = make_photo(user, result_image_path=None, status=PhotoStatus.preview)
    with patch("app.routers.segmentation.storage_service.delete_photo"):
        response = client.delete(f"/edit-photo/{photo.id}/preview", headers=auth_headers)
    assert response.status_code == 204
    assert db.query(Photo).count() == 0
