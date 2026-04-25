FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R app:app /app

USER app

EXPOSE 8001

# Runs Alembic migrations then starts the server.
# Shell form is intentional so ${PORT} expands at runtime.
CMD alembic upgrade head && \
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}
