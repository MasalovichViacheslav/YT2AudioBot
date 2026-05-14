import pytest

from models.delivery import PixeldrainUploadResult
from services.pixeldrain import PixeldrainService, PixeldrainUploadError


@pytest.fixture(scope="session")
def test_file(tmp_path_factory):
    f = tmp_path_factory.mktemp("pixeldrain") / "test.m4a"
    f.write_bytes(b"fake audio content")
    return f


@pytest.fixture(scope="session")
async def upload_result(test_file) -> PixeldrainUploadResult:
    service = PixeldrainService()
    return await service.upload(test_file)


class TestPixeldrainUpload:
    async def test_returns_upload_result(self, upload_result):
        assert isinstance(upload_result, PixeldrainUploadResult)

    async def test_url_is_not_empty(self, upload_result):
        assert upload_result.url != ""

    async def test_url_starts_with_https(self, upload_result):
        assert upload_result.url.startswith("https://")

    async def test_file_id_is_not_empty(self, upload_result):
        assert upload_result.file_id != ""


class TestPixeldrainUploadError:
    async def test_raises_when_file_not_found(self, tmp_path):
        service = PixeldrainService()
        with pytest.raises(PixeldrainUploadError):
            await service.upload(tmp_path / "nonexistent.m4a")
