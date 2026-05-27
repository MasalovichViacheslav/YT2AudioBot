from unittest.mock import AsyncMock, patch

import pytest
from aiogram.exceptions import TelegramRetryAfter

from bot.routers.audio import _progress_watcher
from models.video import ProgressState


@pytest.fixture
def progress_msg():
    msg = AsyncMock()
    msg.edit_text = AsyncMock()
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
