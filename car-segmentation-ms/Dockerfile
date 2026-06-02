# pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime ships Python 3.10, PyTorch 2.9.1,
# CUDA 12.8, and cuDNN 9 - matches the sam-microservice requirements.
# Cloud Run GPU (NVIDIA L4) supports CUDA 12.x natively.
FROM pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime

WORKDIR /app

# git is required to install segment-anything from GitHub.
# libglib2.0-0 and libgl1-mesa-glx are runtime deps for opencv-python-headless.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        libglib2.0-0 \
        libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

# torch/torchvision/torchaudio are already provided by the base image.
# Filter them out of requirements.txt before installing to avoid pip trying to
# pull the PyPI variants and conflicting with the pre-installed wheels.
COPY requirements.txt .
RUN grep -vE "^(torch|torchvision|torchaudio|#|[[:space:]]*$)" requirements.txt \
        > /tmp/requirements-no-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-no-torch.txt

COPY server.py segmentation.py utils.py ./
COPY model/sam_vit_h_4b8939.pth model/yolov10n.pt ./model/
RUN mkdir -p output && chown -R app:app /app

USER app

<<<<<<< HEAD
# Model weights are downloaded from the GCS bucket in MODEL_BUCKET at startup.
# For local development without MODEL_BUCKET, place weights in ./model/ manually.

EXPOSE 8000

# Use a shell for Cloud Run's PORT expansion, then replace it with uvicorn so
# termination signals reach the server directly.
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
=======
# Model weights are baked into the image to avoid a runtime bucket download.

EXPOSE 8000

# Shell form so ${PORT} expands from the Cloud Run-injected PORT env var.
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
>>>>>>> 81e17ab068b83971db188396d0af1845e2a8bef3
