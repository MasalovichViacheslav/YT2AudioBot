import shutil

import pytest

from models.video import AudioFormat, ProgressState
from services.downloader import DownloaderService
from services.metadata import MetadataService

# The 1st ever YouTube video, uploaded April 23, 2005 by YouTube co-founder.
TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


@pytest.fixture(scope="session")
def test_url() -> str:
    return TEST_URL


@pytest.fixture(scope="session")
def metadata(test_url):
    return MetadataService().get_metadata(test_url)


@pytest.fixture(scope="session")
def audio_format(metadata) -> AudioFormat:
    return metadata.formats[0]


@pytest.fixture(scope="session")
def downloader() -> DownloaderService:
    return DownloaderService()


@pytest.fixture(scope="session")
def downloaded_file(downloader, audio_format, test_url, tmp_path_factory):
    session_dir = tmp_path_factory.mktemp("downloader_session")
    progress_state = ProgressState()
    file_path = downloader._download_sync(
        test_url, audio_format, session_dir, progress_state
    )
    yield file_path
    shutil.rmtree(session_dir, ignore_errors=True)
