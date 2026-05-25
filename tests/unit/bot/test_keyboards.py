from bot.keyboards import (
    build_cancel_keyboard,
    build_confirm_keyboard,
    build_quality_keyboard,
)
from bot.routers.audio import _build_warning_text, _format_duration, _is_youtube_url
from models.video import AudioFormat


def make_format(quality: str, bitrate: int, size: float, fmt_id: str) -> AudioFormat:
    return AudioFormat(
        quality=quality,
        bitrate_kbps=bitrate,
        estimated_size_mb=size,
        format_id=fmt_id,
        container="m4a",
    )


def make_webm_format(size: float) -> AudioFormat:
    return AudioFormat(
        quality="standard",
        bitrate_kbps=128,
        estimated_size_mb=size,
        format_id="251",
        container="webm",
    )


def make_m4a_format(size: float) -> AudioFormat:
    return AudioFormat(
        quality="standard",
        bitrate_kbps=128,
        estimated_size_mb=size,
        format_id="140",
        container="m4a",
    )


FORMATS_THREE = [
    make_format("economy", 48, 9.0, "139"),
    make_format("standard", 128, 23.0, "140"),
    make_format("high", 256, 46.0, "251"),
]

FORMATS_ONE = [
    make_format("standard", 128, 23.0, "140"),
]


class TestBuildQualityKeyboard:
    def test_three_formats_produce_four_buttons(self):
        keyboard = build_quality_keyboard(FORMATS_THREE)
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons) == 4

    def test_one_format_produces_two_buttons(self):
        keyboard = build_quality_keyboard(FORMATS_ONE)
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons) == 2

    def test_button_text_contains_bitrate(self):
        keyboard = build_quality_keyboard(FORMATS_ONE)
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert "128" in buttons[0].text

    def test_button_text_contains_size(self):
        keyboard = build_quality_keyboard(FORMATS_ONE)
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert "23.0" in buttons[0].text

    def test_each_button_on_separate_row(self):
        keyboard = build_quality_keyboard(FORMATS_THREE)
        assert len(keyboard.inline_keyboard) == 4

    def test_has_cancel_button(self):
        keyboard = build_quality_keyboard(FORMATS_THREE)
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert any("Cancel" in btn.text for btn in buttons)


class TestBuildConfirmKeyboard:
    def test_has_exactly_two_buttons(self):
        keyboard = build_confirm_keyboard()
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons) == 2

    def test_both_buttons_in_one_row(self):
        keyboard = build_confirm_keyboard()
        assert len(keyboard.inline_keyboard) == 1

    def test_has_yes_button(self):
        keyboard = build_confirm_keyboard()
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert any("Yes" in btn.text for btn in buttons)

    def test_has_cancel_button(self):
        keyboard = build_confirm_keyboard()
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert any("Cancel" in btn.text for btn in buttons)


class TestIsYoutubeUrl:
    def test_full_url(self):
        assert _is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_short_url(self):
        assert _is_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_url_without_protocol(self):
        assert _is_youtube_url("youtube.com/watch?v=dQw4w9WgXcQ")

    def test_url_with_si_param(self):
        assert _is_youtube_url("https://youtu.be/dQw4w9WgXcQ?si=abc123")

    def test_plain_text(self):
        assert not _is_youtube_url("привет как дела")

    def test_other_url(self):
        assert not _is_youtube_url("https://vimeo.com/123456")

    def test_empty_string(self):
        assert not _is_youtube_url("")


class TestFormatDuration:
    def test_seconds_only(self):
        assert _format_duration(45) == "0:45"

    def test_minutes_and_seconds(self):
        assert _format_duration(143) == "2:23"

    def test_pads_seconds_with_zero(self):
        assert _format_duration(63) == "1:03"

    def test_with_hours(self):
        assert _format_duration(3661) == "1:01:01"

    def test_hours_not_padded(self):
        assert _format_duration(36000) == "10:00:00"


class TestBuildWarningText:
    def test_no_warning_for_small_m4a(self):
        fmt = make_m4a_format(20.0)
        assert _build_warning_text(fmt, 50) is None

    def test_warning_for_large_m4a(self):
        fmt = make_m4a_format(100.0)
        assert _build_warning_text(fmt, 50) is not None

    def test_warning_for_webm_small(self):
        fmt = make_webm_format(20.0)
        assert _build_warning_text(fmt, 50) is not None

    def test_warning_for_large_webm(self):
        fmt = make_webm_format(100.0)
        assert _build_warning_text(fmt, 50) is not None

    def test_large_file_warning_mentions_pixeldrain(self):
        fmt = make_m4a_format(100.0)
        text = _build_warning_text(fmt, 50)
        assert text is not None
        assert "Pixeldrain" in text

    def test_webm_warning_mentions_ios(self):
        fmt = make_webm_format(20.0)
        text = _build_warning_text(fmt, 50)
        assert text is not None
        assert "iOS" in text

    def test_combined_warning_mentions_both(self):
        fmt = make_webm_format(100.0)
        text = _build_warning_text(fmt, 50)
        assert text is not None
        assert "Pixeldrain" in text
        assert "iOS" in text


class TestBuildCancelKeyboard:
    def test_returns_exactly_one_button(self):
        keyboard = build_cancel_keyboard()
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons) == 1

    def test_button_text_contains_cancel(self):
        keyboard = build_cancel_keyboard()
        button = keyboard.inline_keyboard[0][0]
        assert "Cancel" in button.text
