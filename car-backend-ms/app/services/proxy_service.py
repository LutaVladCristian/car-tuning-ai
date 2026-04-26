import base64
import binascii

import httpx

from config import get_settings

_METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/"
    "service-accounts/default/identity"
)
_MAX_SEGMENTATION_IMAGE_BYTES = 16 * 1024 * 1024


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
    except httpx.HTTPError:
        return None


async def _auth_headers(base_url: str) -> dict[str, str]:
    settings = get_settings()
    token = await _identity_token(base_url)
    if token:
        return {"Authorization": f"Bearer {token}"}

    if settings.REQUIRE_SEGMENTATION_IAM:
        raise httpx.RequestError("Could not fetch identity token for segmentation service.")

    return {}


async def _forward(path: str, files: dict, data: dict, timeout: float) -> bytes:
    settings = get_settings()
    base_url = settings.SEGMENTATION_MS_URL

    headers = await _auth_headers(base_url)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url}{path}",
            files=files,
            data=data,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.content


def _decode_limited_b64(value: object, field_name: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Segmentation response missing {field_name}.")
    if len(value) > _MAX_SEGMENTATION_IMAGE_BYTES * 2:
        raise ValueError(f"Segmentation response field {field_name} is too large.")

    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Segmentation response field {field_name} is invalid base64.") from exc

    if len(decoded) > _MAX_SEGMENTATION_IMAGE_BYTES:
        raise ValueError(f"Segmentation response field {field_name} is too large.")
    return decoded


async def forward_edit_photo(
    content: bytes, filename: str, prompt: str, edit_car: bool, size: str
) -> tuple[bytes, bytes]:
    settings = get_settings()
    base_url = settings.SEGMENTATION_MS_URL

    headers = await _auth_headers(base_url)

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{base_url}/edit-photo",
            files={"file": (filename, content, "image/jpeg")},
            data={"prompt": prompt, "edit_car": str(edit_car).lower(), "size": size},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    return (
        _decode_limited_b64(data.get("result_b64"), "result_b64"),
        _decode_limited_b64(data.get("mask_b64"), "mask_b64"),
    )
