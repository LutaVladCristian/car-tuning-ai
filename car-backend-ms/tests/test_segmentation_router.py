from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.db.models.photo import OperationType, Photo

FAKE_PNG = b"\x89PNG_FAKE_BYTES"
FAKE_JPEG = b"\xff\xd8\xff" + b"\x00" * 10


def _mock_proxy(return_value=FAKE_PNG):
    return AsyncMock(return_value=return_value)


def _http_status_error(status_code: int = 503):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    err = httpx.HTTPStatusError("error", request=MagicMock(), response=mock_response)
    return AsyncMock(side_effect=err)


class TestEditPhoto:
    def test_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/edit-photo",
            files={"file": ("car.jpg", FAKE_JPEG, "image/jpeg")},
            data={"prompt": "p", "edit_car": "true"},
        )
        assert resp.status_code == 401

    def test_success_returns_png_bytes(self, client, auth_headers):
        with patch("app.routers.segmentation.proxy_service.forward_edit_photo", _mock_proxy()):
            resp = client.post(
                "/edit-photo",
                files={"file": ("car.jpg", FAKE_JPEG, "image/jpeg")},
                data={"prompt": "make it red", "edit_car": "true"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert resp.content == FAKE_PNG
        assert resp.headers["content-type"] == "image/png"

    def test_saves_correct_operation_params(self, client, auth_headers, user_and_token, db):
        user, _ = user_and_token
        with patch("app.routers.segmentation.proxy_service.forward_edit_photo", _mock_proxy()):
            client.post(
                "/edit-photo",
                files={"file": ("car.jpg", FAKE_JPEG, "image/jpeg")},
                data={"prompt": "rally livery", "edit_car": "false", "size": "1024x1024"},
                headers=auth_headers,
            )
        photo = db.query(Photo).filter(Photo.user_id == user.id).first()
        assert photo.operation_type == OperationType.edit_photo
        assert photo.operation_params["prompt"] == "rally livery"
        assert photo.operation_params["edit_car"] is False
        assert photo.operation_params["size"] == "1024x1024"

    def test_defaults_size_to_auto(self, client, auth_headers, user_and_token, db):
        user, _ = user_and_token
        with patch("app.routers.segmentation.proxy_service.forward_edit_photo", _mock_proxy()):
            client.post(
                "/edit-photo",
                files={"file": ("car.jpg", FAKE_JPEG, "image/jpeg")},
                data={"prompt": "keep resolution", "edit_car": "true"},
                headers=auth_headers,
            )
        photo = db.query(Photo).filter(Photo.user_id == user.id).first()
        assert photo.operation_params["size"] == "auto"

    def test_oversized_file_returns_413(self, client, auth_headers):
        big_jpeg = b"\xff\xd8\xff" + b"\x00" * (10 * 1024 * 1024 + 1)
        resp = client.post(
            "/edit-photo",
            files={"file": ("car.jpg", big_jpeg, "image/jpeg")},
            data={"prompt": "p", "edit_car": "true"},
            headers=auth_headers,
        )
        assert resp.status_code == 413

    def test_invalid_image_type_returns_415(self, client, auth_headers):
        resp = client.post(
            "/edit-photo",
            files={"file": ("doc.txt", b"not an image at all", "text/plain")},
            data={"prompt": "p", "edit_car": "true"},
            headers=auth_headers,
        )
        assert resp.status_code == 415

    def test_5xx_proxy_error_returns_502(self, client, auth_headers):
        with patch("app.routers.segmentation.proxy_service.forward_edit_photo", _http_status_error(503)):
            resp = client.post(
                "/edit-photo",
                files={"file": ("car.jpg", FAKE_JPEG, "image/jpeg")},
                data={"prompt": "p", "edit_car": "true"},
                headers=auth_headers,
            )
        assert resp.status_code == 502

    def test_4xx_proxy_error_passes_through(self, client, auth_headers):
        with patch("app.routers.segmentation.proxy_service.forward_edit_photo", _http_status_error(400)):
            resp = client.post(
                "/edit-photo",
                files={"file": ("car.jpg", FAKE_JPEG, "image/jpeg")},
                data={"prompt": "p", "edit_car": "true"},
                headers=auth_headers,
            )
        assert resp.status_code == 400
