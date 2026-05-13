from dataclasses import dataclass, field


@dataclass
class AudioFormat:
    """Represents an available audio format for a video.

    Attributes:
        quality: Quality level — 'economy', 'standard', or 'high'.
        bitrate_kbps: Actual stream bitrate in kbps.
        estimated_size_mb: Estimated file size in MB
                            (duration_sec * bitrate_kbps / 8 / 1024).
        format_id: Internal yt-dlp stream identifier used for downloading.
        container: Audio container format (e.g. 'm4a', 'webm').
    """

    quality: str
    bitrate_kbps: int
    estimated_size_mb: float
    format_id: str
    container: str


@dataclass
class VideoMetadata:
    """Video metadata retrieved without downloading.

    Attributes:
        title: Video title.
        duration_sec: Duration in seconds.
        formats: List of available audio formats, 1 to 3 entries.
    """

    title: str
    duration_sec: int
    formats: list[AudioFormat] = field(default_factory=list)


@dataclass
class ProgressState:
    """Shared state object for communicating download progress.

    Written by the yt-dlp progress_hook (sync thread),
    read by the bot's async observer.

    Attributes:
        percent: Download progress from 0.0 to 100.0.
        speed: Human-readable download speed (e.g. '1.2 MiB/s').
        eta_sec: Estimated seconds until download completes.
        cancelled: Set to True by the bot handler to request cancellation.
        finished: Set to True by progress_hook when download completes.
    """

    percent: float = 0.0
    speed: str = ""
    eta_sec: int = 0
    cancelled: bool = False
    finished: bool = False
