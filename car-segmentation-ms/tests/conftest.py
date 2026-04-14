import os
import sys
from unittest.mock import MagicMock

# Must be set before server.py is imported (checked at module level)
os.environ["OPENAI_API_KEY"] = "test-key"

# Stub the segmentation module so YOLO/SAM model files are never loaded.
# server.py does: from segmentation import segment_car, segment_car_part, working_dir
_mock_seg = MagicMock()
_mock_seg.working_dir = "/tmp/seg_test"
sys.modules["segmentation"] = _mock_seg

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from server import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
