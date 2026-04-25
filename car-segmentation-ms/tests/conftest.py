import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Must be set before server.py is imported (checked at module level)
os.environ["OPENAI_API_KEY"] = "test-key"

# Stub the segmentation module so YOLO/SAM model files are never loaded.
# server.py does: from segmentation import segment_car, segment_car_part, working_dir
_mock_seg = MagicMock()
_mock_seg.working_dir = str(Path(__file__).resolve().parents[1] / "output" / "test-requests")
sys.modules["segmentation"] = _mock_seg

import pytest  # noqa: E402
import server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from server import app  # noqa: E402


@pytest.fixture()
def client():
    server._models_ready.set()
    server._working_dir = _mock_seg.working_dir
    with patch("server._load_models", return_value=None):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
