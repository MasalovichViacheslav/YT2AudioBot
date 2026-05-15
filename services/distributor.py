from pathlib import Path

from loguru import logger

from config.settings import settings
from models.delivery import DeliveryResult
from services.pixeldrain import PixeldrainService


class DistributorError(Exception):
    """Base exception for all distributor errors."""


class DistributorService:
    async def distribute(self, file_path: Path) -> DeliveryResult:
        """Determine delivery method and return DeliveryResult.

        Args:
            file_path: Path to the file to deliver.

        Returns:
            DeliveryResult with method='telegram' or method='pixeldrain'.

        Raises:
            DistributorError: If the file does not exist.
            PixeldrainUploadError: If upload to Pixeldrain fails.
        """
        if not file_path.exists():
            raise DistributorError(f"File not found: {file_path}")

        size_mb = file_path.stat().st_size / 1024 / 1024
        logger.info(
            f"File size: {size_mb:.1f} MB, threshold: {settings.max_file_size_mb} MB"
        )

        if size_mb <= settings.max_file_size_mb:
            logger.info(f"Delivering via Telegram: {file_path.name}")
            return DeliveryResult(method="telegram", file_path=file_path)

        logger.info(f"File exceeds limit, uploading to Pixeldrain: {file_path.name}")
        result = await PixeldrainService().upload(file_path)
        logger.info(f"Delivering via Pixeldrain: {result.url}")
        return DeliveryResult(method="pixeldrain", url=result.url)
