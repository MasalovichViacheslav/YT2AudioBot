from unittest.mock import patch

import pytest
import yt_dlp

from models.video import AudioFormat, ProgressState
from services.downloader import DownloadCancelledError, DownloadError, DownloaderService

TEST_FORMAT = AudioFormat(
    quality="standard",
    bitrate_kbps=128,
    estimated_size_mb=4.7,
    format_id="140",
    container="m4a",
)


@pytest.fixture
def service() -> DownloaderService:
    return DownloaderService()


@pytest.fixture
def progress_state() -> ProgressState:
    return ProgressState()


class TestMakeSessionDir:
    def test_directory_is_created(self, service, tmp_path, mocker):
        mocker.patch("services.downloader.settings.temp_dir", str(tmp_path))
        session_dir = service._make_session_dir()
        assert session_dir.exists()

    def test_each_call_creates_unique_directory(self, service, tmp_path, mocker):
        mocker.patch("services.downloader.settings.temp_dir", str(tmp_path))
        dir1 = service._make_session_dir()
        dir2 = service._make_session_dir()
        assert dir1 != dir2


class TestBuildYdlOpts:
    def test_ydl_opts_structure(self, service, tmp_path, progress_state):
        opts = service._build_ydl_opts(TEST_FORMAT, tmp_path, progress_state)

        assert opts["format"] == "140[format_note*=original]/140[format_note!=DRC]/140"
        assert str(tmp_path) in opts["outtmpl"]
        assert opts["quiet"] is True
        assert opts["no_warnings"] is True
        assert len(opts["progress_hooks"]) == 1
        assert callable(opts["progress_hooks"][0])

    def test_progress_hook_updates_progress_state(
        self, service, tmp_path, progress_state
    ):
        opts = service._build_ydl_opts(TEST_FORMAT, tmp_path, progress_state)
        hook = opts["progress_hooks"][0]

        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 512,
                "total_bytes": 1024,
                "_speed_str": "1.2 MiB/s",
                "eta": 10,
            }
        )

        assert progress_state.percent == 50.0
        assert progress_state.speed == "1.2 MiB/s"
        assert progress_state.eta_sec == 10

    def test_progress_hook_sets_finished(self, service, tmp_path, progress_state):
        opts = service._build_ydl_opts(TEST_FORMAT, tmp_path, progress_state)
        hook = opts["progress_hooks"][0]

        hook({"status": "finished"})

        assert progress_state.finished is True

    def test_progress_hook_raises_on_cancelled(self, service, tmp_path, progress_state):
        progress_state.cancelled = True
        opts = service._build_ydl_opts(TEST_FORMAT, tmp_path, progress_state)
        hook = opts["progress_hooks"][0]

        with pytest.raises(DownloadCancelledError):
            hook(
                {
                    "status": "downloading",
                    "downloaded_bytes": 0,
                    "total_bytes": 1,
                    "_speed_str": "",
                    "eta": 0,
                }
            )

    def test_progress_hook_uses_estimate_when_total_bytes_is_none(
        self, service, tmp_path, progress_state
    ):
        opts = service._build_ydl_opts(TEST_FORMAT, tmp_path, progress_state)
        hook = opts["progress_hooks"][0]

        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 512,
                "total_bytes": None,
                "total_bytes_estimate": 1024,
                "_speed_str": "1.2 MiB/s",
                "eta": 10,
            }
        )

        assert progress_state.percent == 50.0


class TestDownloadSync:
    def test_returns_file_path(self, service, tmp_path, progress_state):
        fake_file_path = tmp_path / "audio.m4a"
        fake_file_path.touch()

        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.download.return_value = None
            result = service._download_sync(
                "https://youtube.com", TEST_FORMAT, tmp_path, progress_state
            )

        assert result == fake_file_path

    def test_raises_download_error_on_yt_dlp_failure(
        self, service, tmp_path, progress_state
    ):
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.download.side_effect = (
                yt_dlp.utils.DownloadError("fail")
            )

            with pytest.raises(DownloadError):
                service._download_sync(
                    "https://youtube.com", TEST_FORMAT, tmp_path, progress_state
                )

    def test_passes_through_download_cancelled_error(
        self, service, tmp_path, progress_state
    ):
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.download.side_effect = (
                DownloadCancelledError("cancelled")
            )

            with pytest.raises(DownloadCancelledError):
                service._download_sync(
                    "https://youtube.com", TEST_FORMAT, tmp_path, progress_state
                )

    def test_raises_download_error_when_no_file_created(
        self, service, tmp_path, progress_state
    ):
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.download.return_value = None

            with pytest.raises(DownloadError, match="no file was created"):
                service._download_sync(
                    "https://youtube.com", TEST_FORMAT, tmp_path, progress_state
                )


class TestDownload:
    @pytest.mark.asyncio
    async def test_returns_tuple_of_paths(
        self, service, tmp_path, progress_state, mocker
    ):
        fake_file_path = tmp_path / "audio.m4a"
        fake_file_path.touch()

        mocker.patch("services.downloader.settings.temp_dir", str(tmp_path))
        mocker.patch.object(service, "_download_sync", return_value=fake_file_path)

        file_path, session_dir = await service.download(
            "https://youtube.com", TEST_FORMAT, progress_state
        )

        assert file_path == fake_file_path
        assert session_dir.exists()

    @pytest.mark.asyncio
    async def test_calls_download_sync_via_executor(
        self, service, tmp_path, progress_state, mocker
    ):
        fake_file_path = tmp_path / "audio.m4a"
        fake_file_path.touch()

        mocker.patch("services.downloader.settings.temp_dir", str(tmp_path))
        mock_sync = mocker.patch.object(
            service, "_download_sync", return_value=fake_file_path
        )

        await service.download("https://youtube.com", TEST_FORMAT, progress_state)

        mock_sync.assert_called_once()
