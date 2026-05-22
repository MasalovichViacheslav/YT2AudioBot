from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.delivery import PixeldrainUploadResult
from services.pixeldrain import PixeldrainService, PixeldrainUploadError


@pytest.fixture
def service():
    return PixeldrainService()


@pytest.fixture
def existing_file(tmp_path):
    f = tmp_path / "test.m4a"
    f.write_bytes(b"fake audio content")
    return f


def make_mock_response(data: dict, status: int = 200):
    response = AsyncMock()
    response.json = AsyncMock(return_value=data)
    response.status = status
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def make_mock_session(response):
    session = AsyncMock()
    session.put = MagicMock(return_value=response)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


class TestPixeldrainUpload:
    async def test_returns_upload_result(self, service, existing_file):
        response = make_mock_response({"id": "abc123"})
        session = make_mock_session(response)

        with patch("services.pixeldrain.aiohttp.ClientSession", return_value=session):
            result = await service.upload(existing_file)

        assert isinstance(result, PixeldrainUploadResult)

    async def test_url_built_from_file_id(self, service, existing_file):
        response = make_mock_response({"id": "abc123"})
        session = make_mock_session(response)

        with patch("services.pixeldrain.aiohttp.ClientSession", return_value=session):
            result = await service.upload(existing_file)

        assert result.url == "https://pixeldrain.com/u/abc123"
        assert result.file_id == "abc123"

    async def test_raises_on_authentication_error(self, service, existing_file):
        response = make_mock_response(
            {"value": "authentication_required", "message": "..."}
        )
        session = make_mock_session(response)

        with (
            patch("services.pixeldrain.aiohttp.ClientSession", return_value=session),
            pytest.raises(PixeldrainUploadError, match="authentication failed"),
        ):
            await service.upload(existing_file)

    async def test_raises_on_unexpected_error(self, service, existing_file):
        response = make_mock_response({"value": "internal", "message": "Server error"})
        session = make_mock_session(response)

        with (
            patch("services.pixeldrain.aiohttp.ClientSession", return_value=session),
            pytest.raises(PixeldrainUploadError, match="Pixeldrain returned error"),
        ):
            await service.upload(existing_file)

    async def test_raises_on_unexpected_response_structure(
        self, service, existing_file
    ):
        response = make_mock_response({"unexpected": "field"})
        session = make_mock_session(response)

        with (
            patch("services.pixeldrain.aiohttp.ClientSession", return_value=session),
            pytest.raises(PixeldrainUploadError, match="Unexpected response structure"),
        ):
            await service.upload(existing_file)

    async def test_raises_on_network_error(self, service, existing_file):
        import aiohttp

        session = AsyncMock()
        session.put = MagicMock(side_effect=aiohttp.ClientError("Network error"))
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("services.pixeldrain.aiohttp.ClientSession", return_value=session),
            pytest.raises(PixeldrainUploadError, match="Upload request failed"),
        ):
            await service.upload(existing_file)

    async def test_raises_when_file_not_found(self, service, tmp_path):
        with pytest.raises(PixeldrainUploadError, match="File not found"):
            await service.upload(tmp_path / "nonexistent.m4a")
