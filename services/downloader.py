import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Any

import yt_dlp
from loguru import logger

from config.settings import settings
from models.video import AudioFormat, ProgressState


class DownloadCancelledError(Exception):
    """Raised when the user cancels an in-progress download."""


class DownloadError(Exception):
    """Raised when yt-dlp fails to download the audio stream."""


class DownloaderService:
    def _make_session_dir(self) -> Path:
        """Create a unique temporary directory for this download session."""
        session_dir = Path(settings.temp_dir) / str(uuid.uuid4())
        session_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Session dir created: {session_dir}")
        return session_dir

    def _build_ydl_opts(
        self,
        audio_format: AudioFormat,
        session_dir: Path,
        progress_state: ProgressState,
    ) -> dict[str, Any]:
        """Build yt-dlp options for downloading a specific audio format."""

        def progress_hook(d: dict[str, Any]) -> None:
            if progress_state.cancelled:
                raise DownloadCancelledError("Download cancelled by user.")

            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                progress_state.percent = float(
                    d.get("downloaded_bytes", 0) / total * 100
                )
                progress_state.speed = d.get("_speed_str", "").strip()
                progress_state.eta_sec = int(d.get("eta", 0) or 0)

            elif d["status"] == "finished":
                progress_state.finished = True

        fmt = audio_format.format_id

        opts: dict[str, Any] = {
            "format": f"{fmt}[format_note!=DRC]/{fmt}",
            "outtmpl": str(session_dir / "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
        }

        if settings.cookies_file:
            tmp_cookies = Path(settings.temp_dir) / "cookies.txt"
            if not tmp_cookies.exists():
                shutil.copy(settings.cookies_file, tmp_cookies)
            opts["cookiefile"] = str(tmp_cookies)

        return opts

    def _download_sync(
        self,
        url: str,
        audio_format: AudioFormat,
        session_dir: Path,
        progress_state: ProgressState,
    ) -> Path:
        """Run yt-dlp synchronously. Intended to be called in a thread pool."""
        ydl_opts = self._build_ydl_opts(audio_format, session_dir, progress_state)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except DownloadCancelledError:
            raise
        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(str(e)) from e

        files = list(session_dir.iterdir())
        if not files:
            raise DownloadError("yt-dlp finished but no file was created.")

        file_path = files[0]
        logger.info(f"Downloaded: {file_path}")
        return file_path

    async def download(
        self,
        url: str,
        audio_format: AudioFormat,
        progress_state: ProgressState,
    ) -> tuple[Path, Path]:
        """Download audio stream and return (file_path, session_dir).

        The caller is responsible for cleaning up session_dir after use.
        """
        session_dir = self._make_session_dir()
        logger.info(f"Starting download: {url}, format={audio_format.format_id}")

        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None,
            self._download_sync,
            url,
            audio_format,
            session_dir,
            progress_state,
        )

        return file_path, session_dir
