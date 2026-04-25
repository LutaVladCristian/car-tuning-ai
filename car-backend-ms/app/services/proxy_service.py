import httpx

from config import get_settings

_METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/"
    "service-accounts/default/identity"
)


async def _identity_token(audience: str) -> str | None:
    """Fetch a GCP-signed identity token for Cloud Run IAM auth. Returns None outside GCP."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                _METADATA_TOKEN_URL,
                params={"audience": audience},
                headers={"Metadata-Flavor": "Google"},
            )
            resp.raise_for_status()
            return resp.text
    except Exception:
        return None


async def _forward(path: str, files: dict, data: dict, timeout: float) -> bytes:
    settings = get_settings()
    base_url = settings.SEGMENTATION_MS_URL

    token = await _identity_token(base_url)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url}{path}",
            files=files,
            data=data,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.content


async def forward_edit_photo(
    content: bytes, filename: str, prompt: str, edit_car: bool, size: str
) -> bytes:
    return await _forward(
        "/edit-photo",
        {"file": (filename, content, "image/jpeg")},
        {"prompt": prompt, "edit_car": str(edit_car).lower(), "size": size},
        timeout=180.0,
    )
