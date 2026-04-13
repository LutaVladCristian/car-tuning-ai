FROM python:3.12-slim

# OpenCV needs libGL; git is required for the SAM install from GitHub
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libgl1 \
        libglib2.0-0 \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch first so the requirements.txt torch==2.2.0 constraint is satisfied
RUN pip install --upgrade pip \
 && pip install --no-cache-dir \
        torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 \
        --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Model weights are NOT baked in — mount at runtime:
#   docker run -v ./car-segmentation-ms/model:/model ...
RUN mkdir -p /app/output

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
