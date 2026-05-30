import pytest
import yt_dlp

from models.video import AudioFormat, VideoMetadata
from services.metadata import MetadataService, VideoUnavailableError

MOCK_FORMATS = [
    {"vcodec": "none", "abr": 48, "format_id": "249", "ext": "webm"},
    {"vcodec": "none", "abr": 128, "format_id": "140", "ext": "m4a"},
    {"vcodec": "none", "abr": 256, "format_id": "251", "ext": "webm"},
    {"vcodec": "av01", "abr": 128, "format_id": "999", "ext": "mp4"},
]

MOCK_INFO = {
    "title": "Test Video",
    "duration": 300,
    "formats": MOCK_FORMATS,
}


@pytest.fixture
def service() -> MetadataService:
    return MetadataService()


@pytest.fixture
def mock_yt_dlp(mocker):
    return mocker.patch("services.metadata.yt_dlp.YoutubeDL")


class TestGetMetadata:
    def test_returns_video_metadata(self, service, mock_yt_dlp):
        ydl_instance = mock_yt_dlp.return_value.__enter__.return_value
        ydl_instance.extract_info.return_value = MOCK_INFO

        result = service.get_metadata("https://youtube.com/watch?v=test")

        assert isinstance(result, VideoMetadata)
        assert result.title == "Test Video"
        assert result.duration_sec == 300

    def test_raises_when_video_unavailable(self, service, mock_yt_dlp):
        ydl_instance = mock_yt_dlp.return_value.__enter__.return_value
        ydl_instance.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "Video unavailable"
        )

        with pytest.raises(VideoUnavailableError):
            service.get_metadata("https://youtube.com/watch?v=test")

    def test_raises_when_info_is_none(self, service, mock_yt_dlp):
        ydl_instance = mock_yt_dlp.return_value.__enter__.return_value
        ydl_instance.extract_info.return_value = None

        with pytest.raises(VideoUnavailableError):
            service.get_metadata("https://youtube.com/watch?v=test")


class TestSelectFormats:
    def test_returns_up_to_three_formats(self, service):
        result = service._select_formats(MOCK_FORMATS, duration_sec=300)

        assert len(result) <= 3

    def test_filters_video_streams(self, service):
        result = service._select_formats(MOCK_FORMATS, duration_sec=300)

        format_ids = [f.format_id for f in result]
        assert "999" not in format_ids

    def test_returns_empty_list_when_no_audio_streams(self, service):
        video_only = [{"vcodec": "av01", "abr": 128, "format_id": "999"}]

        result = service._select_formats(video_only, duration_sec=300)

        assert result == []

    def test_deduplicates_formats(self, service):
        """Ensure that when multiple quality targets map to the same stream,
        it appears only once in the result.

        Example: only one stream at 128kbps is available. All three targets
        (48, 128, 256 kbps) will pick it as the closest. The result should
        contain one AudioFormat, not three.
        """
        single_stream = [{"vcodec": "none", "abr": 128, "format_id": "140"}]

        result = service._select_formats(single_stream, duration_sec=300)

        assert len(result) == 1

    def test_estimated_size_is_correct(self, service):
        streams = [{"vcodec": "none", "abr": 128, "format_id": "140"}]

        result = service._select_formats(streams, duration_sec=300)

        assert result[0].estimated_size_mb == 4.7

    def test_returns_audio_format_instances(self, service):
        result = service._select_formats(MOCK_FORMATS, duration_sec=300)

        assert all(isinstance(f, AudioFormat) for f in result)

    def test_prefers_m4a_over_webm(self, service):
        result = service._select_formats(MOCK_FORMATS, duration_sec=300)
        assert all(f.container == "m4a" for f in result)

    def test_falls_back_to_mp3_when_no_m4a(self, service):
        streams = [
            {"vcodec": "none", "abr": 128, "format_id": "140", "ext": "mp3"},
            {"vcodec": "none", "abr": 256, "format_id": "251", "ext": "webm"},
        ]
        result = service._select_formats(streams, duration_sec=300)
        assert all(f.container == "mp3" for f in result)

    def test_falls_back_to_webm_when_no_m4a_or_mp3(self, service):
        streams = [
            {"vcodec": "none", "abr": 128, "format_id": "251", "ext": "webm"},
        ]
        result = service._select_formats(streams, duration_sec=300)
        assert all(f.container == "webm" for f in result)

    def test_container_is_set_correctly(self, service):
        streams = [{"vcodec": "none", "abr": 128, "format_id": "140", "ext": "m4a"}]
        result = service._select_formats(streams, duration_sec=300)
        assert result[0].container == "m4a"

    def test_filters_drc_formats(self, service):
        streams = [
            {
                "vcodec": "none",
                "abr": 128,
                "format_id": "140",
                "ext": "m4a",
                "format_note": "",
            },
            {
                "vcodec": "none",
                "abr": 128,
                "format_id": "140-drc",
                "ext": "m4a",
                "format_note": "DRC",
            },
            {
                "vcodec": "none",
                "abr": 128,
                "format_id": "141-drc",
                "ext": "m4a",
                "format_note": "",
            },
        ]

        result = service._select_formats(streams, duration_sec=300)

        format_ids = [f.format_id for f in result]
        assert "140-drc" not in format_ids
        assert "141-drc" not in format_ids
