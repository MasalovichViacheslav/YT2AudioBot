from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from config.settings import settings
from services.invite import InviteService


class WhitelistMiddleware(BaseMiddleware):
    def __init__(self, invite_service: InviteService) -> None:
        self._invite_service = invite_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if (
            isinstance(event, Message)
            and event.text
            and event.text.strip() == f"/start {settings.invite_token}"
        ):
            return await handler(event, data)

        user = None

        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if user is None:
            return None

        if user.id in settings.allowed_user_ids:
            return await handler(event, data)

        if self._invite_service.has_access(user.id):
            return await handler(event, data)

        logger.warning(f"Ignoring request from unauthorized user: {user.id}")
        if isinstance(event, Message):
            await event.answer("⛔ You don't have access to this bot.")
        elif isinstance(event, CallbackQuery):
            await event.answer("⛔ You don't have access to this bot.", show_alert=True)

        return None
