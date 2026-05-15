from dataclasses import dataclass
from pathlib import Path


@dataclass
class PixeldrainUploadResult:
    """Represents the result of a file upload to Pixeldrain.

    Attributes:
        url: Public download page link to the uploaded file.
        file_id: Pixeldrain internal file identifier.
    """

    url: str
    file_id: str


@dataclass
class DeliveryResult:
    """Represents the result of a file delivery decision.

    Attributes:
        method: Delivery method — 'telegram' or 'pixeldrain'.
        file_path: Path to the file (only for method='telegram').
        url: Public link to the file (only for method='pixeldrain').
    """

    method: str
    file_path: Path | None = None
    url: str | None = None
