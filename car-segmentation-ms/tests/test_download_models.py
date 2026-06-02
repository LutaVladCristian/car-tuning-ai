import sys
from pathlib import Path
from unittest.mock import MagicMock

import download_models
import pytest


def test_download_models_skips_bucket_when_weights_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(download_models, "_MODEL_DIR", tmp_path)
    for filename in download_models._MODELS:
        (tmp_path / filename).write_bytes(b"weight")

    download_models.download_models()


def test_download_models_requires_bucket_when_weights_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(download_models, "_MODEL_DIR", tmp_path)
    monkeypatch.delenv("MODEL_BUCKET", raising=False)

    with pytest.raises(RuntimeError, match="MODEL_BUCKET is not set"):
        download_models.download_models()


def test_download_models_fetches_only_missing_weights(tmp_path, monkeypatch):
    monkeypatch.setattr(download_models, "_MODEL_DIR", tmp_path)
    monkeypatch.setenv("MODEL_BUCKET", "models")
    existing = download_models._MODELS[0]
    missing = download_models._MODELS[1]
    (tmp_path / existing).write_bytes(b"existing")

    blob = MagicMock()
    blob.download_to_filename.side_effect = lambda filename: Path(filename).write_bytes(b"downloaded")
    bucket = MagicMock()
    bucket.blob.return_value = blob
    client = MagicMock()
    client.bucket.return_value = bucket

    storage = MagicMock()
    storage.Client.return_value = client
    monkeypatch.setitem(sys.modules, "google.cloud.storage", storage)

    download_models.download_models()

    client.bucket.assert_called_once_with("models")
    bucket.blob.assert_called_once_with(missing)
    assert (tmp_path / missing).read_bytes() == b"downloaded"
