from pathlib import Path

from loguru import logger
from mutagen.id3 import COMM, ID3, TIT2  # type: ignore[attr-defined]
from mutagen.mp4 import MP4


class TaggerError(Exception):
    """Raised when tagging fails (corrupted file, unsupported format, etc.)."""


class TaggerService:
    def tag(self, file_path: Path, title: str, url: str) -> None:
        """Write title and source URL tags into an audio file.

        Supports .m4a and .mp3 containers. .webm is skipped (not supported by mutagen).

        Args:
            file_path: Path to the audio file.
            title: Video title to write as the track title tag.
            url: Original YouTube URL to write as the comment tag.

        Raises:
            TaggerError: If the extension is unsupported or mutagen fails.
        """
        ext = file_path.suffix.lower()

        if ext == ".webm":
            logger.warning(
                f"Tagging not supported for WebM files, skipping: {file_path.name}"
            )
            return

        try:
            if ext == ".m4a":
                self._tag_m4a(file_path, title, url)
            elif ext == ".mp3":
                self._tag_mp3(file_path, title, url)
            else:
                raise TaggerError(f"Unsupported file extension: {ext!r}")
        except TaggerError:
            raise
        except Exception as e:
            logger.error(f"Failed to tag {file_path}: {e}")
            raise TaggerError(f"Failed to tag {file_path.name}: {e}") from e

        logger.info(f"Tagged: {file_path.name!r} — title={title!r}")

    def _tag_m4a(self, file_path: Path, title: str, url: str) -> None:
        audio = MP4(file_path)  # type: ignore[no-untyped-call]
        audio["\xa9nam"] = [title]
        audio["\xa9cmt"] = [url]
        audio.save()  # type: ignore[no-untyped-call]

    def _tag_mp3(self, file_path: Path, title: str, url: str) -> None:
        audio = ID3(file_path)  # type: ignore[no-untyped-call]
        audio.add(TIT2(encoding=3, text=title))  # type: ignore[no-untyped-call]
        audio.add(COMM(encoding=3, lang="eng", desc="", text=url))  # type: ignore[no-untyped-call]
        audio.save(file_path)
