import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.proxy_service import forward_generate_photo, forward_segment_photo

FAKE = b"\x89PNG_FAKE"


def _client(json_body):
    response = MagicMock()
    response.json.return_value = json_body
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get = AsyncMock(side_effect=Exception("metadata unavailable"))
    client.post = AsyncMock(return_value=response)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, client


@pytest.mark.asyncio
async def test_forward_segment_photo_returns_three_images():
    encoded = base64.b64encode(FAKE).decode()
    ctx, client = _client({"image_b64": encoded, "raw_mask_b64": encoded, "mask_b64": encoded})
    with patch("app.services.proxy_service._auth_headers", AsyncMock(return_value={})), patch(
        "app.services.proxy_service.httpx.AsyncClient", return_value=ctx
    ):
        assert await forward_segment_photo(b"img", "car.jpg", "image/jpeg", True, "auto") == (FAKE, FAKE, FAKE)
    assert client.post.call_args.kwargs["data"]["edit_car"] == "true"
    assert client.post.call_args.kwargs["files"]["file"] == ("car.jpg", b"img", "image/jpeg")


@pytest.mark.asyncio
async def test_forward_generate_photo_returns_result():
    encoded = base64.b64encode(FAKE).decode()
    ctx, client = _client({"result_b64": encoded})
    with patch("app.services.proxy_service._auth_headers", AsyncMock(return_value={})), patch(
        "app.services.proxy_service.httpx.AsyncClient", return_value=ctx
    ):
        assert await forward_generate_photo(b"image", b"mask", "red", "auto") == FAKE
    assert client.post.call_args.kwargs["data"]["prompt"] == "red"
