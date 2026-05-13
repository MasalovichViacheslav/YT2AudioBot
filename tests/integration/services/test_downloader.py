import pytest

from models.video import ProgressState
from services.downloader import DownloadCancelledError


class TestDownloaderService:
    def test_file_is_downloaded(self, downloaded_file):
        assert downloaded_file.exists()

    def test_file_has_m4a_extension(self, downloaded_file):
        assert downloaded_file.suffix == ".m4a"

    def test_file_size_is_greater_than_zero(self, downloaded_file):
        assert downloaded_file.stat().st_size > 0

    def test_cancellation_stops_download(
        self, downloader, audio_format, test_url, tmp_path
    ):
        progress_state = ProgressState(cancelled=True)
        with pytest.raises(DownloadCancelledError):
            downloader._download_sync(test_url, audio_format, tmp_path, progress_state)
