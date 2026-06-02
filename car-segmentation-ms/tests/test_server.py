import base64
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from openai import BadRequestError
from PIL import Image


def _png(size=(10, 10)):
    output = io.BytesIO()
    Image.new("RGBA", size, (0, 0, 0, 0)).save(output, format="PNG")
    return output.getvalue()


PNG = _png()


def test_segment_photo_returns_prepared_and_both_masks(client):
    def segment(content, edit_car, size, output_dir=None):
        for name in ("image.png", "raw-mask.png", "mask.png"):
            (Path(output_dir) / name).write_bytes(PNG)

    with patch("server._segment_car", side_effect=segment):
        response = client.post("/segment-photo", files={"file": ("car.png", PNG, "image/png")}, data={"edit_car": "true"})
    assert response.status_code == 200
    assert set(response.json()) == {"image_b64", "raw_mask_b64", "mask_b64"}


def test_generate_photo_calls_openai_after_approval(client):
    result = MagicMock()
    result.data = [MagicMock(b64_json=base64.b64encode(PNG).decode())]
    api = MagicMock()
    api.images.edit.return_value = result
    with patch("server.client", api):
        response = client.post("/generate-photo", files={"file": ("image.png", PNG, "image/png"), "mask": ("mask.png", PNG, "image/png")}, data={"prompt": "red", "size": "auto"})
    assert response.status_code == 200
    assert "result_b64" in response.json()
    call_kwargs = api.images.edit.call_args.kwargs
    assert call_kwargs["prompt"] == "red"
    assert call_kwargs["image"] == ("image.png", PNG, "image/png")
    assert call_kwargs["mask"] == ("mask.png", PNG, "image/png")


def test_generate_photo_reports_openai_rejection(client):
    request = httpx.Request("POST", "https://api.openai.com/v1/images/edits")
    response = httpx.Response(400, request=request)
    api = MagicMock()
    api.images.edit.side_effect = BadRequestError("invalid image", response=response, body=None)
    with patch("server.client", api):
        result = client.post("/generate-photo", files={"file": ("image.png", PNG, "image/png"), "mask": ("mask.png", PNG, "image/png")}, data={"prompt": "red", "size": "auto"})
    assert result.status_code == 502
    assert result.json()["detail"] == "OpenAI rejected the prepared image or mask. Please try another image."
