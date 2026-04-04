from pathlib import Path


def get_user_storage_dir(base_storage_path: str, user_id: int) -> Path:
    path = Path(base_storage_path) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_bytes_to_disk(directory: Path, filename: str, data: bytes) -> str:
    full_path = directory / filename
    full_path.write_bytes(data)
    return str(full_path)


def get_extension(filename: str | None) -> str:
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return "jpg"
