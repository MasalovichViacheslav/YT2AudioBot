from typing import Any

import yt_dlp
from loguru import logger

from config.settings import settings
from models.video import AudioFormat, VideoMetadata


class VideoUnavailableError(Exception):
    """Raised when a video is unavailable, private, or age-restricted."""


class VideoDurationError(Exception):
    """Raised when a video exceeds the maximum allowed duration."""


class MetadataService:
    """Fetches video metadata from YouTube without downloading."""

    _QUALITY_TARGETS: dict[str, int] = {
        "economy": 48,
        "standard": 128,
        "high": 256,
    }

    def get_metadata(self, url: str) -> VideoMetadata:
        """Fetch video metadata for a given YouTube URL.

        Args:
            url: YouTube video URL.

        Returns:
            VideoMetadata with title, duration, and available audio formats.

        Raises:
            VideoUnavailableError: If the video is unavailable, private,
            or age-restricted.
            VideoDurationError: If the video exceeds MAX_VIDEO_DURATION_SEC.
        """
        logger.info(f"Fetching metadata for {url}")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            raise VideoUnavailableError(str(e)) from e

        if info is None:
            raise VideoUnavailableError("No metadata returned for this URL.")

        duration: int = info.get("duration", 0)
        if duration > settings.max_video_duration_sec:
            raise VideoDurationError(
                f"Video duration {duration}s exceeds limit "
                f"{settings.max_video_duration_sec}s."
            )

        title: str = info.get("title", "Unknown")
        formats = self._select_formats(info.get("formats", []), duration)

        logger.info(f"Metadata fetched: '{title}', {duration}s, {len(formats)} formats")
        return VideoMetadata(title=title, duration_sec=duration, formats=formats)

    def _select_formats(
        self, raw_formats: list[dict[str, Any]], duration_sec: int
    ) -> list[AudioFormat]:
        """Select up to three audio formats closest to target bitrates.

        Prefers m4a streams for broad device compatibility, falls back to mp3,
        then webm if neither is available.

        Args:
            raw_formats: Raw format list from yt-dlp.
            duration_sec: Video duration in seconds, used to estimate file size.

        Returns:
            List of AudioFormat, 1 to 3 entries, ordered from lowest to highest quality.
        """
        audio_streams = [
            f
            for f in raw_formats
            if f.get("vcodec") == "none" and f.get("abr") is not None
        ]

        if not audio_streams:
            return []

        m4a_streams = [f for f in audio_streams if f.get("ext") == "m4a"]
        mp3_streams = [f for f in audio_streams if f.get("ext") == "mp3"]

        if m4a_streams:
            selected_streams = m4a_streams
        elif mp3_streams:
            selected_streams = mp3_streams
        else:
            selected_streams = audio_streams

        result: list[AudioFormat] = []
        seen_format_ids: set[str] = set()

        for quality, target_kbps in self._QUALITY_TARGETS.items():
            closest = min(
                selected_streams,
                key=lambda f: abs(f["abr"] - target_kbps),
            )

            if closest["format_id"] in seen_format_ids:
                continue

            seen_format_ids.add(closest["format_id"])
            actual_kbps = int(closest["abr"])
            estimated_size_mb = round(duration_sec * actual_kbps / 8 / 1024, 1)

            result.append(
                AudioFormat(
                    quality=quality,
                    bitrate_kbps=actual_kbps,
                    estimated_size_mb=estimated_size_mb,
                    format_id=closest["format_id"],
                    container=closest.get("ext", "m4a"),
                )
            )

        return result
