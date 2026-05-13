from models.video import AudioFormat, VideoMetadata


class TestMetadataService:
    def test_returns_video_metadata(self, metadata):
        assert isinstance(metadata, VideoMetadata)

    def test_title_is_not_empty(self, metadata):
        assert metadata.title != ""

    def test_duration_is_positive(self, metadata):
        assert metadata.duration_sec > 0

    def test_has_at_least_one_format(self, metadata):
        assert len(metadata.formats) > 0

    def test_formats_are_audio_format_instances(self, metadata):
        assert all(isinstance(f, AudioFormat) for f in metadata.formats)

    def test_format_bitrate_is_positive(self, metadata):
        assert all(f.bitrate_kbps > 0 for f in metadata.formats)

    def test_format_size_is_positive(self, metadata):
        assert all(f.estimated_size_mb > 0 for f in metadata.formats)

    def test_formats_prefer_m4a(self, metadata):
        containers = [f.container for f in metadata.formats]
        if "m4a" in containers:
            assert containers[0] == "m4a"
