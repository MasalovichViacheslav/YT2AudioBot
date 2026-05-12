import pytest

from models.video import AudioFormat, VideoMetadata
from services.metadata import MetadataService, VideoUnavailableError

# The 1st ever YouTube video, uploaded April 23, 2005 by YouTube co-founder.
TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


@pytest.fixture(scope="session")
def service() -> MetadataService:
    return MetadataService()


@pytest.fixture(scope="session")
def metadata(service) -> VideoMetadata:
    return service.get_metadata(TEST_URL)


class TestMetadataService:
    def test_returns_video_metadata(self, metadata):
        assert isinstance(metadata, VideoMetadata)

    def test_title_is_not_empty(self, metadata):
        assert metadata.title

    def test_duration_is_positive(self, metadata):
        assert metadata.duration_sec > 0

    def test_returns_at_least_one_format(self, metadata):
        assert len(metadata.formats) >= 1

    def test_formats_are_audio_format_instances(self, metadata):
        assert all(isinstance(f, AudioFormat) for f in metadata.formats)

    def test_formats_fields_are_parsed_from_response(self, metadata):
        assert all(f.bitrate_kbps > 0 for f in metadata.formats)
        assert all(f.estimated_size_mb > 0 for f in metadata.formats)

    def test_raises_on_invalid_url(self, service):
        with pytest.raises(VideoUnavailableError):
            service.get_metadata("https://www.youtube.com/watch?v=invalid_id_xyz")
