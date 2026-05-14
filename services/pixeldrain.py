from pathlib import Path

import aiohttp
from loguru import logger

from config.settings import settings
from models.delivery import PixeldrainUploadResult


class PixeldrainError(Exception):
    """Base exception for Pixeldrain errors."""


class PixeldrainUploadError(PixeldrainError):
    """Raised when file upload fails."""


class PixeldrainService:
    _BASE_URL = "https://pixeldrain.com/api/file"

    async def upload(self, file_path: Path) -> PixeldrainUploadResult:
        if not file_path.exists():
            raise PixeldrainUploadError(f"File not found: {file_path}")

        logger.info(f"Uploading to Pixeldrain: {file_path.name}")

        timeout = aiohttp.ClientTimeout(total=settings.pixeldrain_timeout_sec)
        upload_url = f"{self._BASE_URL}/{file_path.name}"
        auth = aiohttp.BasicAuth(login="", password=settings.pixeldrain_api_key)

        try:
            async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
                with file_path.open("rb") as f:
                    async with session.put(upload_url, data=f) as response:
                        data = await response.json()
        except aiohttp.ClientError as e:
            raise PixeldrainUploadError(f"Upload request failed: {e}") from e

        if "value" in data:
            if data.get("value") == "authentication_required":
                raise PixeldrainUploadError(
                    "Pixeldrain authentication failed — "
                    "API key may be missing or expired"
                )
            raise PixeldrainUploadError(f"Pixeldrain returned error: {data}")

        try:
            file_id = data["id"]
        except (KeyError, TypeError) as e:
            raise PixeldrainUploadError(f"Unexpected response structure: {data}") from e

        url = f"https://pixeldrain.com/u/{file_id}"
        result = PixeldrainUploadResult(url=url, file_id=file_id)
        logger.info(f"Uploaded to Pixeldrain: {result.url}")
        return result
