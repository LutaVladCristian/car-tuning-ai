import base64
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


def _make_png(size=(10, 10)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", size, color=(0, 0, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


FAKE_PNG = _make_png()


class TestEditPhoto:
    @pytest.fixture()
    def openai_mock(self):
        """Patch segment_car and the OpenAI client for /edit-photo tests.

        C3: server.py now creates its own temp dir and passes it as output_dir
        to segment_car. The mock writes image/mask files there.
        """
        fake_b64 = base64.b64encode(FAKE_PNG).decode()

        def _fake_segment(content, edit_car, size, *args, output_dir=None, **kwargs):
            if output_dir:
                (Path(output_dir) / "image.png").write_bytes(FAKE_PNG)
                (Path(output_dir) / "mask.png").write_bytes(FAKE_PNG)

        mock_result = MagicMock()
        mock_result.data = [MagicMock(b64_json=fake_b64)]
        mock_client = MagicMock()
        mock_client.images.edit.return_value = mock_result

        with (
            patch("server.segment_car", side_effect=_fake_segment),
            patch("server.client", mock_client),
        ):
            yield mock_client

    def test_success_returns_png(self, client, openai_mock):
        resp = client.post(
            "/edit-photo",
            files={"file": ("car.png", FAKE_PNG, "image/png")},
            data={"prompt": "make it red", "edit_car": "true"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_openai_called_with_prompt_and_auto_size(self, client, openai_mock):
        client.post(
            "/edit-photo",
            files={"file": ("car.png", FAKE_PNG, "image/png")},
            data={"prompt": "rally livery", "edit_car": "false"},
        )
        call_kwargs = openai_mock.images.edit.call_args.kwargs
        assert call_kwargs["prompt"] == "rally livery"
        assert call_kwargs["size"] == "auto"

    def test_auto_size_preserves_source_dimensions(self, client):
        source_png = _make_png((20, 12))
        edited_png = _make_png((8, 8))
        fake_b64 = base64.b64encode(edited_png).decode()

        def _fake_segment(content, edit_car, size, *args, output_dir=None, **kwargs):
            assert size is None
            if output_dir:
                (Path(output_dir) / "image.png").write_bytes(source_png)
                (Path(output_dir) / "mask.png").write_bytes(source_png)

        mock_result = MagicMock()
        mock_result.data = [MagicMock(b64_json=fake_b64)]
        mock_client = MagicMock()
        mock_client.images.edit.return_value = mock_result

        with (
            patch("server.segment_car", side_effect=_fake_segment),
            patch("server.client", mock_client),
        ):
            resp = client.post(
                "/edit-photo",
                files={"file": ("car.png", source_png, "image/png")},
                data={"prompt": "keep size", "edit_car": "true"},
            )

        assert resp.status_code == 200
        assert Image.open(io.BytesIO(resp.content)).size == (20, 12)

    def test_openai_error_returns_500(self, client):
        def _fake_segment(content, edit_car, size, *args, output_dir=None, **kwargs):
            if output_dir:
                (Path(output_dir) / "image.png").write_bytes(FAKE_PNG)
                (Path(output_dir) / "mask.png").write_bytes(FAKE_PNG)

        mock_client = MagicMock()
        mock_client.images.edit.side_effect = RuntimeError("OpenAI down")

        with (
            patch("server.segment_car", side_effect=_fake_segment),
            patch("server.client", mock_client),
        ):
            resp = client.post(
                "/edit-photo",
                files={"file": ("car.png", FAKE_PNG, "image/png")},
                data={"prompt": "p", "edit_car": "true", "size": "1024x1024"},
            )
        assert resp.status_code == 500
