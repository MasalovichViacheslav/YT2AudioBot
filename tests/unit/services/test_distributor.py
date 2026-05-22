from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from models.delivery import PixeldrainUploadResult
from services.distributor import DistributorError, DistributorService


@pytest.fixture
def service() -> DistributorService:
    return DistributorService()


@pytest.fixture
def small_file(tmp_path: Path) -> Path:
    f = tmp_path / "audio.m4a"
    f.write_bytes(b"x" * 1024)
    return f


@pytest.fixture
def large_file(tmp_path: Path) -> Path:
    f = tmp_path / "audio.m4a"
    f.write_bytes(b"x" * (51 * 1024 * 1024))
    return f


class TestDistribute:
    async def test_small_file_returns_telegram(self, service, small_file):
        result = await service.distribute(small_file)

        assert result.method == "telegram"
        assert result.file_path == small_file
        assert result.url is None

    async def test_large_file_returns_pixeldrain(self, service, large_file):
        mock_upload = AsyncMock(
            return_value=PixeldrainUploadResult(
                url="https://pixeldrain.com/u/abc123",
                file_id="abc123",
            )
        )

        with patch("services.distributor.PixeldrainService.upload", mock_upload):
            result = await service.distribute(large_file)

        assert result.method == "pixeldrain"
        assert result.url == "https://pixeldrain.com/u/abc123"
        assert result.file_path is None

    async def test_raises_when_file_not_found(self, service, tmp_path):
        with pytest.raises(DistributorError):
            await service.distribute(tmp_path / "nonexistent.m4a")
