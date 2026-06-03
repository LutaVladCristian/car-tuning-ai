FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R app:app /app

USER app

EXPOSE 8001

# Shell form is intentional so ${PORT} expands at runtime.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}
