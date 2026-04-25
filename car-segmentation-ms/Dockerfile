# pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime ships Python 3.10, PyTorch 2.2.0,
# CUDA 11.8, and cuDNN 8 — matches the sam-microservice conda env exactly.
# Cloud Run GPU (NVIDIA L4) runs CUDA 12.x hardware but is backward-compatible
# with CUDA 11.8 containers.
FROM pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# git is required to install segment-anything from GitHub.
# libglib2.0-0 and libgl1-mesa-glx are runtime deps for opencv-python-headless.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        libglib2.0-0 \
        libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# torch/torchvision/torchaudio are already provided by the base image.
# Filter them out of requirements.txt before installing to avoid pip trying to
# pull the PyPI (CUDA) variants and conflicting with the pre-installed wheels.
COPY requirements.txt .
RUN grep -vE "^(torch|torchvision|torchaudio|#|[[:space:]]*$)" requirements.txt \
        > /tmp/requirements-no-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-no-torch.txt

COPY server.py segmentation.py utils.py download_models.py ./

# Model weights are NOT baked into the image.
# At startup, download_models.py fetches them from the GCS bucket in MODEL_BUCKET.
# For local dev without MODEL_BUCKET set, place weights in ./model/ manually.

EXPOSE 8000

# download_models.py runs first; if MODEL_BUCKET is unset it exits immediately.
# Shell form so ${PORT} expands from the Cloud Run-injected PORT env var.
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
