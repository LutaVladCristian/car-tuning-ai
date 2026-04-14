from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.proxy_service import (
    forward_car_part_segmentation,
    forward_car_segmentation,
    forward_edit_photo,
)

FAKE_PNG = b"\x89PNG_FAKE_BYTES"


def _make_async_client(status_code=200, content=FAKE_PNG):
    """Build a patched httpx.AsyncClient context manager."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.content = content
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, mock_client


@pytest.mark.asyncio
class TestForwardCarSegmentation:
    async def test_returns_response_bytes_on_success(self):
        ctx, _ = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            result = await forward_car_segmentation(b"img", "car.jpg", False)
        assert result == FAKE_PNG

    async def test_forwards_inverse_false_as_string(self):
        ctx, mock_client = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            await forward_car_segmentation(b"img", "car.jpg", False)
        _, kwargs = mock_client.post.call_args
        assert kwargs["data"]["inverse"] == "false"

    async def test_forwards_inverse_true_as_string(self):
        ctx, mock_client = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            await forward_car_segmentation(b"img", "car.jpg", True)
        _, kwargs = mock_client.post.call_args
        assert kwargs["data"]["inverse"] == "true"

    async def test_raises_http_status_error_on_4xx(self):
        ctx, _ = _make_async_client(status_code=400)
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(httpx.HTTPStatusError):
                await forward_car_segmentation(b"img", "car.jpg", False)

    async def test_raises_http_status_error_on_5xx(self):
        ctx, _ = _make_async_client(status_code=500)
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(httpx.HTTPStatusError):
                await forward_car_segmentation(b"img", "car.jpg", False)


@pytest.mark.asyncio
class TestForwardCarPartSegmentation:
    async def test_returns_response_bytes_on_success(self):
        ctx, _ = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            result = await forward_car_part_segmentation(b"img", "car.jpg", 5, False)
        assert result == FAKE_PNG

    async def test_forwards_car_part_id_and_inverse(self):
        ctx, mock_client = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            await forward_car_part_segmentation(b"img", "car.jpg", 22, True)
        _, kwargs = mock_client.post.call_args
        assert kwargs["data"]["carPartId"] == "22"
        assert kwargs["data"]["inverse"] == "true"

    async def test_raises_on_error_status(self):
        ctx, _ = _make_async_client(status_code=422)
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(httpx.HTTPStatusError):
                await forward_car_part_segmentation(b"img", "car.jpg", 5, False)


@pytest.mark.asyncio
class TestForwardEditPhoto:
    async def test_returns_response_bytes_on_success(self):
        ctx, _ = _make_async_client()
        with patch("app.services.proxy_service.httpx.AsyncClient", return_value=ctx):
            result = await forward_edit_photo(b"img", "car.jpg", "make it red", True, "1024x1024")
        assert result == FAKE_PNG

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
