import httpx

from config import get_settings


# M8: Single internal helper avoids repeating timeout/URL construction logic.
async def _forward(path: str, files: dict, data: dict, timeout: float) -> bytes:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{settings.SEGMENTATION_MS_URL}{path}",
            files=files,
            data=data,
        )
        resp.raise_for_status()
        return resp.content


async def forward_car_segmentation(content: bytes, filename: str, inverse: bool) -> bytes:
    return await _forward(
        "/car-segmentation",
        {"file": (filename, content, "image/jpeg")},
        {"inverse": str(inverse).lower()},
        timeout=120.0,
    )


async def forward_car_part_segmentation(
    content: bytes, filename: str, car_part_id: int, inverse: bool
) -> bytes:
    return await _forward(
        "/car-part-segmentation",
        {"file": (filename, content, "image/jpeg")},
        {"carPartId": str(car_part_id), "inverse": str(inverse).lower()},
        timeout=120.0,
    )


async def forward_edit_photo(
    content: bytes, filename: str, prompt: str, edit_car: bool, size: str
) -> bytes:
    return await _forward(
        "/edit-photo",
        {"file": (filename, content, "image/jpeg")},
        {"prompt": prompt, "edit_car": str(edit_car).lower(), "size": size},
        timeout=180.0,
    )
