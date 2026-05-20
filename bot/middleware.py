from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from config.settings import settings


class WhitelistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None

        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if user is None or user.id not in settings.allowed_user_ids:
            if user is not None:
                logger.warning(f"Ignoring request from unauthorized user: {user.id}")
                if isinstance(event, Message):
                    await event.answer("⛔ You don't have access to this bot.")
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "⛔ You don't have access to this bot.", show_alert=True
                    )
            return None

        return await handler(event, data)
