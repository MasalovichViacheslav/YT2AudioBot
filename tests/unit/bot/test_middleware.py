from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message

from bot.middleware import WhitelistMiddleware

ALLOWED_ID = 123456789
STRANGER_ID = 999999999


@pytest.fixture
def middleware() -> WhitelistMiddleware:
    return WhitelistMiddleware()


@pytest.fixture
def handler() -> AsyncMock:
    return AsyncMock()


def make_message(user_id: int | None) -> MagicMock:
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    if user_id is None:
        message.from_user = None
    else:
        message.from_user = MagicMock()
        message.from_user.id = user_id
    return message


class TestWhitelistMiddleware:
    async def test_allowed_user_calls_handler(self, middleware, handler):
        message = make_message(ALLOWED_ID)

        with patch("bot.middleware.settings.allowed_user_ids", [ALLOWED_ID]):
            await middleware(handler, message, {})

        handler.assert_called_once()

    async def test_stranger_does_not_call_handler(self, middleware, handler):
        message = make_message(STRANGER_ID)

        with patch("bot.middleware.settings.allowed_user_ids", [ALLOWED_ID]):
            await middleware(handler, message, {})

        handler.assert_not_called()

    async def test_no_from_user_does_not_call_handler(self, middleware, handler):
        message = make_message(None)

        with patch("bot.middleware.settings.allowed_user_ids", [ALLOWED_ID]):
            await middleware(handler, message, {})

        handler.assert_not_called()

    async def test_stranger_receives_answer(self, middleware, handler):
        message = make_message(STRANGER_ID)

        with patch("bot.middleware.settings.allowed_user_ids", [ALLOWED_ID]):
            await middleware(handler, message, {})

        message.answer.assert_called_once()
