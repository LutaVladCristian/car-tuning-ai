"""
Downloads SAM and YOLO model weights from a GCS bucket at container startup.
If MODEL_BUCKET env var is not set, skips download (local dev: models in ./model/).
"""
import os
import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).parent / "model"
_MODELS = ["sam_vit_h_4b8939.pth", "yolo11n.pt"]


def download_models() -> None:
    _MODEL_DIR.mkdir(exist_ok=True)

    missing = [f for f in _MODELS if not (_MODEL_DIR / f).exists()]
    if not missing:
        print("  All model files already present, skipping download")
        return

    bucket_name = os.getenv("MODEL_BUCKET")
    if not bucket_name:
        raise RuntimeError(
            f"Missing model files {missing} and MODEL_BUCKET is not set. "
            "Place the weights manually in car-segmentation-ms/model/ for local development."
        )

    from google.cloud import storage
    try:
        client = storage.Client()
    except Exception as exc:
        raise RuntimeError(
            f"Missing model files {missing} but cannot authenticate with GCS. "
            "For local dev, place the weights directly in car-segmentation-ms/model/ "
            "instead of relying on MODEL_BUCKET. "
            f"GCS error: {exc}"
        ) from exc

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
