from unittest.mock import AsyncMock

import pytest

from bot.routers.audio import _READY_MSG, start
from bot.states import AudioStates


@pytest.fixture
def message():
    msg = AsyncMock()
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def state():
    s = AsyncMock()
    s.set_state = AsyncMock()
    return s


class TestStartHandler:
    async def test_sets_waiting_for_url_state(self, message, state):
        state.get_state = AsyncMock(return_value=AudioStates.waiting_for_url)

        await start(message, state)

        state.set_state.assert_awaited_once_with(AudioStates.waiting_for_url)

    async def test_sends_ready_message(self, message, state):
        state.get_state = AsyncMock(return_value=AudioStates.waiting_for_url)

        await start(message, state)

        message.answer.assert_awaited_once_with(_READY_MSG)

    async def test_ignores_when_choosing_quality(self, message, state):
        state.get_state = AsyncMock(return_value=AudioStates.choosing_quality)

        await start(message, state)

        state.set_state.assert_not_awaited()
        message.answer.assert_not_awaited()

    async def test_ignores_when_downloading(self, message, state):
        state.get_state = AsyncMock(return_value=AudioStates.downloading)

        await start(message, state)

        state.set_state.assert_not_awaited()
        message.answer.assert_not_awaited()
