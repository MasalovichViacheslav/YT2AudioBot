from unittest.mock import AsyncMock

import pytest

from bot.routers.audio import start
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
        await start(message, state)

        state.set_state.assert_awaited_once_with(AudioStates.waiting_for_url)

    async def test_sends_welcome_message(self, message, state):
        await start(message, state)

        message.answer.assert_awaited_once()
