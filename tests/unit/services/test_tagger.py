import pytest

from services.tagger import TaggerError, TaggerService

TITLE = "Test Video"
URL = "https://www.youtube.com/watch?v=test"


@pytest.fixture
def service() -> TaggerService:
    return TaggerService()


class TestTagM4a:
    def test_tags_are_written(self, service, tmp_path, mocker):
        file_path = tmp_path / "audio.m4a"
        file_path.touch()

        mock_mp4 = mocker.MagicMock()
        mocker.patch("services.tagger.MP4", return_value=mock_mp4)

        service.tag(file_path, TITLE, URL)

        mock_mp4.__setitem__.assert_any_call("\xa9nam", [TITLE])
        mock_mp4.__setitem__.assert_any_call("\xa9cmt", [URL])
        mock_mp4.save.assert_called_once()


class TestTagMp3:
    def test_tags_are_written(self, service, tmp_path, mocker):
        file_path = tmp_path / "audio.mp3"
        file_path.touch()

        mock_id3 = mocker.MagicMock()
        mocker.patch("services.tagger.ID3", return_value=mock_id3)

        service.tag(file_path, TITLE, URL)

        mock_id3.add.assert_called()
        mock_id3.save.assert_called_once_with(file_path)


class TestTagWebm:
    def test_tagging_is_skipped_and_file_is_not_modified(self, service, tmp_path):
        file_path = tmp_path / "audio.webm"
        file_path.write_bytes(b"\x1aE\xdf\xa3")
        original_bytes = file_path.read_bytes()

        service.tag(file_path, TITLE, URL)

        assert file_path.read_bytes() == original_bytes


class TestTagUnsupported:
    def test_raises_tagger_error(self, service, tmp_path):
        file_path = tmp_path / "audio.flac"
        file_path.write_bytes(b"fake")

        with pytest.raises(TaggerError):
            service.tag(file_path, TITLE, URL)


class TestTagCorrupted:
    def test_raises_tagger_error_on_corrupted_m4a(self, service, tmp_path):
        file_path = tmp_path / "corrupted.m4a"
        file_path.write_bytes(b"this is not a valid m4a file")

        with pytest.raises(TaggerError):
            service.tag(file_path, TITLE, URL)

    def test_raises_tagger_error_on_corrupted_mp3(self, service, tmp_path):
        file_path = tmp_path / "corrupted.mp3"
        file_path.write_bytes(b"this is not a valid mp3 file")

        with pytest.raises(TaggerError):
            service.tag(file_path, TITLE, URL)
