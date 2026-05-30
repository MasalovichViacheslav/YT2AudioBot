from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
)

from bot.routers.audio import _deliver, _progress_watcher, _safe_edit
from models.delivery import DeliveryResult
from models.video import ProgressState


@pytest.fixture
def progress_msg():
    msg = AsyncMock()
    msg.edit_text = AsyncMock()
    return msg


@pytest.fixture
def message():
    msg = AsyncMock()
    msg.answer_audio = AsyncMock()
    return msg


class TestProgressWatcher:
    async def test_stops_when_finished(self, progress_msg):
        progress_state = ProgressState(finished=True)

        await _progress_watcher(progress_msg, progress_state)

        progress_msg.edit_text.assert_not_called()

    async def test_stops_when_cancelled(self, progress_msg):
        progress_state = ProgressState(cancelled=True)

        await _progress_watcher(progress_msg, progress_state)

        progress_msg.edit_text.assert_not_called()

    async def test_updates_message_with_progress(self, progress_msg):
        progress_state = ProgressState(percent=50.0, speed="2.0 MiB/s", eta_sec=10)

        async def finish_after_one_tick(*args, **kwargs):
            progress_state.finished = True

        progress_msg.edit_text.side_effect = finish_after_one_tick

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await _progress_watcher(progress_msg, progress_state)

        progress_msg.edit_text.assert_called_once()
        call_text = progress_msg.edit_text.call_args[0][0]
        assert "50%" in call_text
        assert "2.0 MiB/s" in call_text
        assert "ETA 10s" in call_text

    async def test_does_not_raise_on_edit_text_exception(self, progress_msg):
        progress_state = ProgressState(percent=30.0)
        call_count = 0

        async def fail_then_finish(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                progress_state.finished = True
            raise Exception("Message was deleted")

        progress_msg.edit_text.side_effect = fail_then_finish

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await _progress_watcher(progress_msg, progress_state)

    async def test_waits_on_retry_after(self, progress_msg):
        progress_state = ProgressState(percent=50.0, speed="2.0 MiB/s", eta_sec=10)
        call_count = 0

        async def retry_then_finish(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TelegramRetryAfter(retry_after=1)
            progress_state.finished = True

        progress_msg.edit_text.side_effect = retry_then_finish

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await _progress_watcher(progress_msg, progress_state)

        assert call_count == 2


class TestSafeEdit:
    async def test_edits_message_successfully(self, progress_msg):
        await _safe_edit(progress_msg, "some text")

        progress_msg.edit_text.assert_awaited_once_with("some text")

    async def test_does_not_raise_on_telegram_bad_request(self, progress_msg):
        progress_msg.edit_text.side_effect = TelegramBadRequest(
            method=MagicMock(), message="message to edit not found"
        )

        await _safe_edit(progress_msg, "some text")

    async def test_does_not_raise_on_telegram_network_error(self, progress_msg):
        progress_msg.edit_text.side_effect = TelegramNetworkError(
            method=MagicMock(), message="Request timeout error"
        )

        await _safe_edit(progress_msg, "some text")


class TestDeliver:
    async def test_telegram_method_sends_audio(self, message, progress_msg, tmp_path):
        audio_file = tmp_path / "audio.m4a"
        audio_file.write_bytes(b"fake audio")

        delivery = DeliveryResult(method="telegram", file_path=audio_file)

        with patch("bot.routers.audio.FSInputFile"):
            await _deliver(message, progress_msg, delivery, "Test Title")

        message.answer_audio.assert_awaited_once()

    async def test_telegram_method_deletes_progress_msg_after_upload(
        self, message, progress_msg, tmp_path
    ):
        audio_file = tmp_path / "audio.m4a"
        audio_file.write_bytes(b"fake audio")

        delivery = DeliveryResult(method="telegram", file_path=audio_file)

        call_order = []
        message.answer_audio.side_effect = lambda **kwargs: call_order.append(
            "answer_audio"
        )
        progress_msg.delete.side_effect = lambda: call_order.append("delete")

        with patch("bot.routers.audio.FSInputFile"):
            await _deliver(message, progress_msg, delivery, "Test Title")

        assert call_order == ["answer_audio", "delete"]

    async def test_telegram_method_does_not_delete_progress_msg_on_network_error(
        self, message, progress_msg, tmp_path
    ):
        audio_file = tmp_path / "audio.m4a"
        audio_file.write_bytes(b"fake audio")

        delivery = DeliveryResult(method="telegram", file_path=audio_file)

        message.answer_audio.side_effect = TelegramNetworkError(
            method=MagicMock(), message="Request timeout error"
        )

        with (
            patch("bot.routers.audio.FSInputFile"),
            pytest.raises(TelegramNetworkError),
        ):
            await _deliver(message, progress_msg, delivery, "Test Title")

        progress_msg.delete.assert_not_awaited()

    async def test_pixeldrain_method_edits_progress_msg_with_url(
        self, message, progress_msg
    ):
        delivery = DeliveryResult(
            method="pixeldrain", url="https://pixeldrain.com/u/abc123"
        )

        await _deliver(message, progress_msg, delivery, "Test Title")

        progress_msg.edit_text.assert_awaited_once()
        call_text = progress_msg.edit_text.call_args[0][0]
        assert "https://pixeldrain.com/u/abc123" in call_text

    async def test_pixeldrain_method_does_not_send_audio(self, message, progress_msg):
        delivery = DeliveryResult(
            method="pixeldrain", url="https://pixeldrain.com/u/abc123"
        )

        await _deliver(message, progress_msg, delivery, "Test Title")

        message.answer_audio.assert_not_awaited()

    async def test_telegram_method_passes_title(self, message, progress_msg, tmp_path):
        audio_file = tmp_path / "audio.m4a"
        audio_file.write_bytes(b"fake audio")

        delivery = DeliveryResult(method="telegram", file_path=audio_file)

        with patch("bot.routers.audio.FSInputFile"):
            await _deliver(message, progress_msg, delivery, "My Track Title")

        _, kwargs = message.answer_audio.call_args
        assert kwargs.get("title") == "My Track Title"
