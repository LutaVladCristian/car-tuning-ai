"""
Downloads SAM and YOLO model weights from a GCS bucket at container startup.
If MODEL_BUCKET env var is not set, skips download (local dev: models in ./model/).
"""
import os
import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).parent / "model"
_MODELS = ["sam_vit_h_4b8939.pth", "yolov10n.pt"]


def download_models() -> None:
    bucket_name = os.getenv("MODEL_BUCKET")
    if not bucket_name:
        print("MODEL_BUCKET not set — skipping download, expecting models in ./model/")
        return

    _MODEL_DIR.mkdir(exist_ok=True)

    missing = [f for f in _MODELS if not (_MODEL_DIR / f).exists()]
    if not missing:
        print("  All model files already present, skipping download")
        return

    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for filename in missing:
        dest = _MODEL_DIR / filename
        print(f"  Downloading {filename} from gs://{bucket_name}/{filename} ...")
        bucket.blob(filename).download_to_filename(str(dest))
        size_gb = dest.stat().st_size / 1e9
        print(f"  {filename} done ({size_gb:.2f} GB)")


if __name__ == "__main__":
    download_models()
    sys.exit(0)
