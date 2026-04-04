import httpx

from config import get_settings


async def forward_car_segmentation(content: bytes, filename: str, inverse: bool) -> bytes:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.SEGMENTATION_MS_URL}/car-segmentation",
            files={"file": (filename, content, "image/jpeg")},
            data={"inverse": str(inverse).lower()},
        )
        resp.raise_for_status()
        return resp.content


async def forward_car_part_segmentation(
    content: bytes, filename: str, car_part_id: int, inverse: bool
) -> bytes:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.SEGMENTATION_MS_URL}/car-part-segmentation",
            files={"file": (filename, content, "image/jpeg")},
            data={"carPartId": str(car_part_id), "inverse": str(inverse).lower()},
        )
        resp.raise_for_status()
        return resp.content


async def forward_edit_photo(
    content: bytes, filename: str, prompt: str, edit_car: bool, size: str
) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{settings.SEGMENTATION_MS_URL}/edit-photo",
            files={"file": (filename, content, "image/jpeg")},
            data={"prompt": prompt, "edit_car": str(edit_car).lower(), "size": size},
        )
        resp.raise_for_status()
        return resp.json()
