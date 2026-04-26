import base64
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.proxy_service import forward_edit_photo
from config import get_settings

FAKE_PNG = b"\x89PNG_FAKE_BYTES"
FAKE_MASK = b"\x89PNG_FAKE_MASK"

_FAKE_JSON = {
    "result_b64": base64.b64encode(FAKE_PNG).decode(),
    "mask_b64": base64.b64encode(FAKE_MASK).decode(),
}


def _make_async_client(status_code=200, json_body=_FAKE_JSON):
    """Build a patched httpx.AsyncClient context manager."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_body
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("metadata unavailable"))
    mock_client.post = AsyncMock(return_value=mock_resp)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, mock_client


@pytest.mark.asyncio
class TestForwardEditPhoto:
    async def test_returns_response_bytes_on_success(self):
        ctx, _ = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            result, mask = await forward_edit_photo(b"img", "car.jpg", "make it red", True, "1024x1024")
        assert result == FAKE_PNG
        assert mask == FAKE_MASK

    async def test_forwards_all_params(self):
        ctx, mock_client = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            await forward_edit_photo(b"img", "car.jpg", "rally livery", False, "auto")
        _, kwargs = mock_client.post.call_args
        assert kwargs["data"]["prompt"] == "rally livery"
        assert kwargs["data"]["edit_car"] == "false"
        assert kwargs["data"]["size"] == "auto"

    async def test_raises_on_error_status(self):
        ctx, _ = _make_async_client(status_code=400)
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(httpx.HTTPStatusError):
                await forward_edit_photo(b"img", "car.jpg", "make it blue", True, "1024x1024")

    async def test_invalid_base64_response_raises_value_error(self):
        ctx, _ = _make_async_client(json_body={"result_b64": "not-base64", "mask_b64": _FAKE_JSON["mask_b64"]})
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(ValueError, match="invalid base64"):
                await forward_edit_photo(b"img", "car.jpg", "make it blue", True, "1024x1024")

    async def test_requires_identity_token_when_configured(self, monkeypatch):
        monkeypatch.setenv("REQUIRE_SEGMENTATION_IAM", "true")
        get_settings.cache_clear()
        ctx, _ = _make_async_client()
        try:
            with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
                with pytest.raises(httpx.RequestError):
                    await forward_edit_photo(b"img", "car.jpg", "make it blue", True, "1024x1024")
        finally:
            monkeypatch.delenv("REQUIRE_SEGMENTATION_IAM", raising=False)
            get_settings.cache_clear()
