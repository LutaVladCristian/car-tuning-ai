import base64
import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

# A minimal valid RGBA numpy array that PIL can convert to PNG
FAKE_ARRAY = np.zeros((10, 10, 4), dtype=np.uint8)

FAKE_PNG = _png_bytes = None


def _make_png() -> bytes:
    """Encode FAKE_ARRAY to PNG bytes once."""
    buf = io.BytesIO()
    Image.fromarray(FAKE_ARRAY).save(buf, format="PNG")
    return buf.getvalue()


FAKE_PNG = _make_png()


def _fake_segment_car(*_args, **_kwargs):
    return FAKE_ARRAY.copy()


def _fake_segment_car_part(*_args, **_kwargs):
    return FAKE_ARRAY.copy()


class TestCarSegmentation:
    def test_success_returns_png(self, client):
        with patch("server.segment_car", side_effect=_fake_segment_car):
            resp = client.post(
                "/car-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"inverse": "false"},
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_response_body_is_valid_png(self, client):
        with patch("server.segment_car", side_effect=_fake_segment_car):
            resp = client.post(
                "/car-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"inverse": "false"},
            )
        # Should be decodable as an image
        img = Image.open(io.BytesIO(resp.content))
        assert img.format == "PNG"

    def test_inverse_true_forwarded(self, client):
        captured = {}

        def _capture(content, inverse, *args, **kwargs):
            captured["inverse"] = inverse
            return FAKE_ARRAY.copy()

        with patch("server.segment_car", side_effect=_capture):
            client.post(
                "/car-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"inverse": "true"},
            )
        assert captured["inverse"] is True

    def test_segment_car_error_returns_500(self, client):
        with patch("server.segment_car", side_effect=RuntimeError("model failure")):
            resp = client.post(
                "/car-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"inverse": "false"},
            )
        assert resp.status_code == 500


class TestCarPartSegmentation:
    def test_success_returns_png(self, client):
        with patch("server.segment_car_part", side_effect=_fake_segment_car_part):
            resp = client.post(
                "/car-part-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"carPartId": "22", "inverse": "false"},
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_car_part_id_and_inverse_forwarded(self, client):
        captured = {}

        def _capture(content, car_part_id, inverse, *args, **kwargs):
            captured["car_part_id"] = car_part_id
            captured["inverse"] = inverse
            return FAKE_ARRAY.copy()

        with patch("server.segment_car_part", side_effect=_capture):
            client.post(
                "/car-part-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"carPartId": "5", "inverse": "true"},
            )
        assert captured["car_part_id"] == 5
        assert captured["inverse"] is True

    def test_segment_error_returns_500(self, client):
        with patch("server.segment_car_part", side_effect=ValueError("bad input")):
            resp = client.post(
                "/car-part-segmentation",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"carPartId": "22", "inverse": "false"},
            )
        assert resp.status_code == 500


class TestEditPhoto:
    @pytest.fixture()
    def openai_mock(self, tmp_path):
        """Patch segment_car (writes image/mask files) and the OpenAI client."""
        fake_b64 = base64.b64encode(FAKE_PNG).decode()

        def _fake_segment(content, edit_car, size, *args, **kwargs):
            # Write placeholder files that server.py opens
            (tmp_path / "image.png").write_bytes(FAKE_PNG)
            (tmp_path / "mask.png").write_bytes(FAKE_PNG)

        mock_result = MagicMock()
        mock_result.data = [MagicMock(b64_json=fake_b64)]

        mock_client = MagicMock()
        mock_client.images.edit.return_value = mock_result

        with (
            patch("server.segment_car", side_effect=_fake_segment),
            patch("server.working_dir", str(tmp_path)),
            patch("server.client", mock_client),
        ):
            yield mock_client

    def test_success_returns_png(self, client, openai_mock):
        resp = client.post(
            "/edit-photo",
            files={"file": ("car.jpg", b"img", "image/jpeg")},
            data={"prompt": "make it red", "edit_car": "true", "size": "1024x1024"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_openai_called_with_prompt(self, client, openai_mock):
        client.post(
            "/edit-photo",
            files={"file": ("car.jpg", b"img", "image/jpeg")},
            data={"prompt": "rally livery", "edit_car": "false", "size": "1024x1024"},
        )
        call_kwargs = openai_mock.images.edit.call_args.kwargs
        assert call_kwargs["prompt"] == "rally livery"

    def test_openai_error_returns_500(self, client, tmp_path):
        def _fake_segment(content, edit_car, size, *args, **kwargs):
            (tmp_path / "image.png").write_bytes(FAKE_PNG)
            (tmp_path / "mask.png").write_bytes(FAKE_PNG)

        mock_client = MagicMock()
        mock_client.images.edit.side_effect = RuntimeError("OpenAI down")

        with (
            patch("server.segment_car", side_effect=_fake_segment),
            patch("server.working_dir", str(tmp_path)),
            patch("server.client", mock_client),
        ):
            resp = client.post(
                "/edit-photo",
                files={"file": ("car.jpg", b"img", "image/jpeg")},
                data={"prompt": "p", "edit_car": "true", "size": "1024x1024"},
            )
        assert resp.status_code == 500
