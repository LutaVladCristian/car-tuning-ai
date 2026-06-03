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


def _jpeg(size=(10, 10)):
    output = io.BytesIO()
    Image.new("RGB", size, (255, 0, 0)).save(output, format="JPEG")
    return output.getvalue()


def _gif(size=(10, 10)):
    output = io.BytesIO()
    Image.new("P", size).save(output, format="GIF")
    return output.getvalue()


PNG = _png()
JPEG = _jpeg()
GIF = _gif()


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


def test_segment_photo_rejects_oversized_upload(client):
    response = client.post("/segment-photo", files={"file": ("car.png", b"x" * ((10 * 1024 * 1024) + 1), "image/png")}, data={"edit_car": "true"})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Maximum size is 10 MB."


def test_segment_photo_rejects_unsupported_upload_format(client):
    response = client.post("/segment-photo", files={"file": ("car.gif", GIF, "image/gif")}, data={"edit_car": "true"})
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported or invalid image file. Upload a JPEG, PNG, or WEBP file."


def test_generate_photo_rejects_non_png_mask(client):
    response = client.post("/generate-photo", files={"file": ("image.png", PNG, "image/png"), "mask": ("mask.jpg", JPEG, "image/jpeg")}, data={"prompt": "red", "size": "auto"})
    assert response.status_code == 415
    assert response.json()["detail"] == "Invalid mask image. Upload a PNG file with an alpha channel."


def test_generate_photo_rejects_mask_without_alpha(client):
    opaque_png = io.BytesIO()
    Image.new("RGB", (10, 10), (255, 255, 255)).save(opaque_png, format="PNG")
    response = client.post("/generate-photo", files={"file": ("image.png", PNG, "image/png"), "mask": ("mask.png", opaque_png.getvalue(), "image/png")}, data={"prompt": "red", "size": "auto"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid mask image. Upload a PNG file with an alpha channel."


def test_generate_photo_rejects_mismatched_mask_dimensions(client):
    response = client.post("/generate-photo", files={"file": ("image.png", PNG, "image/png"), "mask": ("mask.png", _png((8, 8)), "image/png")}, data={"prompt": "red", "size": "auto"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Prepared image and mask must have exactly the same dimensions."


def test_generate_photo_rejects_oversized_mask(client):
    response = client.post("/generate-photo", files={"file": ("image.png", PNG, "image/png"), "mask": ("mask.png", b"x" * ((4 * 1024 * 1024) + 1), "image/png")}, data={"prompt": "red", "size": "auto"})
    assert response.status_code == 413
    assert response.json()["detail"] == "Mask image is too large. Maximum size is 4 MB."
