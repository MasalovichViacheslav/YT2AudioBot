from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message

from bot.middleware import WhitelistMiddleware
from services.invite import InviteService


@pytest.fixture
def invite_service() -> InviteService:
    return InviteService()


@pytest.fixture
def middleware(invite_service: InviteService) -> WhitelistMiddleware:
    return WhitelistMiddleware(invite_service)


@pytest.fixture
def handler() -> AsyncMock:
    return AsyncMock()


def make_message(user_id: int) -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = user_id
    return message


async def call_middleware(
    middleware: WhitelistMiddleware,
    handler: AsyncMock,
    user_id: int,
    flags: dict[str, Any] | None = None,
) -> Any:
    event = make_message(user_id)
    data: dict[str, Any] = {}
    if flags:
        data["handler"] = MagicMock()
        data["handler"].flags = flags
    return await middleware(handler, event, data)


class TestWhitelistMiddleware:
    async def test_allows_user_in_permanent_whitelist(
        self, middleware: WhitelistMiddleware, handler: AsyncMock
    ) -> None:
        with patch("bot.middleware.settings") as mock_settings:
            mock_settings.allowed_user_ids = [123]
            await call_middleware(middleware, handler, user_id=123)

        handler.assert_awaited_once()

    async def test_blocks_unknown_user(
        self, middleware: WhitelistMiddleware, handler: AsyncMock
    ) -> None:
        with patch("bot.middleware.settings") as mock_settings:
            mock_settings.allowed_user_ids = []
            event = make_message(999)
            event.answer = AsyncMock()
            data: dict[str, Any] = {}

            await middleware(handler, event, data)

        handler.assert_not_awaited()

    async def test_allows_user_with_active_temporary_session(
        self,
        middleware: WhitelistMiddleware,
        handler: AsyncMock,
        invite_service: InviteService,
    ) -> None:
        invite_service.grant_access(456)

        with patch("bot.middleware.settings") as mock_settings:
            mock_settings.allowed_user_ids = []
            await call_middleware(middleware, handler, user_id=456)

        handler.assert_awaited_once()

    async def test_blocks_user_with_expired_session(
        self,
        middleware: WhitelistMiddleware,
        handler: AsyncMock,
        invite_service: InviteService,
    ) -> None:
        from datetime import UTC, datetime, timedelta
        from unittest.mock import patch as dt_patch

        with dt_patch("services.invite.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
            invite_service.grant_access(456)

            mock_dt.now.return_value = datetime(
                2026, 1, 1, 12, 0, 0, tzinfo=UTC
            ) + timedelta(hours=25)

            with patch("bot.middleware.settings") as mock_settings:
                mock_settings.allowed_user_ids = []
                event = make_message(456)
                event.answer = AsyncMock()
                data: dict[str, Any] = {}

                await middleware(handler, event, data)

        handler.assert_not_awaited()

    async def test_allows_handler_with_allow_unauthorized_flag(
        self, middleware: WhitelistMiddleware, handler: AsyncMock
    ) -> None:
        with patch("bot.middleware.settings") as mock_settings:
            mock_settings.allowed_user_ids = []
            await call_middleware(
                middleware, handler, user_id=999, flags={"allow_unauthorized": True}
            )

        handler.assert_awaited_once()
