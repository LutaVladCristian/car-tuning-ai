"""Download missing SAM and YOLO model weights from GCS at startup."""

import os
from pathlib import Path

_MODEL_DIR = Path(__file__).parent / "model"
_MODELS = ("sam_vit_h_4b8939.pth", "yolov10n.pt")


def download_models() -> None:
    _MODEL_DIR.mkdir(exist_ok=True)
    missing = [filename for filename in _MODELS if not (_MODEL_DIR / filename).exists()]
    if not missing:
        print("All model files already present, skipping download")
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
            "For local development, place the weights directly in car-segmentation-ms/model/. "
            f"GCS error: {exc}"
        ) from exc

    bucket = client.bucket(bucket_name)
    for filename in missing:
        destination = _MODEL_DIR / filename
        print(f"Downloading {filename} from gs://{bucket_name}/{filename} ...")
        bucket.blob(filename).download_to_filename(str(destination))
        print(f"{filename} done ({destination.stat().st_size / 1e9:.2f} GB)")
