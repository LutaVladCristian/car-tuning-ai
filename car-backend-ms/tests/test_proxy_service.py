from types import SimpleNamespace

import pytest

from app.services import proxy_service


class FakeResponse:
    content = b"png-bytes"

    def raise_for_status(self):
        return None


class FakeAsyncClient:
    last_post = None

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def post(self, url, files, data):
        FakeAsyncClient.last_post = {
            "timeout": self.timeout,
            "url": url,
            "files": files,
            "data": data,
        }
        return FakeResponse()


@pytest.mark.asyncio
async def test_forward_edit_photo_posts_expected_multipart_payload(monkeypatch):
    monkeypatch.setattr(proxy_service.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        proxy_service,
        "get_settings",
        lambda: SimpleNamespace(SEGMENTATION_MS_URL="http://segmentation.test"),
    )

    result = await proxy_service.forward_edit_photo(
        b"image-bytes",
        "car.jpg",
        "paint it red",
        True,
        "1024x1536",
    )

    assert result == b"png-bytes"
    assert FakeAsyncClient.last_post == {
        "timeout": 180.0,
        "url": "http://segmentation.test/edit-photo",
        "files": {"file": ("car.jpg", b"image-bytes", "image/jpeg")},
        "data": {
            "prompt": "paint it red",
            "edit_car": "true",
            "size": "1024x1536",
        },
    }
