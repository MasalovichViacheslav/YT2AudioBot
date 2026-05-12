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
    """

    quality: str
    bitrate_kbps: int
    estimated_size_mb: float
    format_id: str


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
