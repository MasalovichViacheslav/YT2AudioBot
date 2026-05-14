from dataclasses import dataclass


@dataclass
class PixeldrainUploadResult:
    """Represents the result of a file upload to Pixeldrain.

    Attributes:
        url: Public download page link to the uploaded file.
        file_id: Pixeldrain internal file identifier.
    """

    url: str
    file_id: str
