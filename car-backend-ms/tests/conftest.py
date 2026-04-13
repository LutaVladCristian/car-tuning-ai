import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-characters")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("SEGMENTATION_MS_URL", "http://segmentation.test")
