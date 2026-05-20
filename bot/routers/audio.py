from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from config.settings import settings
from services.invite import InviteService

router = Router()


@router.message(CommandStart(deep_link=True), flags={"allow_unauthorized": True})
async def start_with_token(message: Message, invite_service: InviteService) -> None:
    if message.from_user is None:
        return

    user_id = message.from_user.id
    token = message.text.split()[-1] if message.text else ""

    if token != settings.invite_token:
        await message.answer("⛔ Invalid invite link.")
        return

    if not invite_service.is_enabled():
        await message.answer("⛔ Invite access is currently disabled.")
        return

    expires_at = invite_service.grant_access(user_id)

    if expires_at is None:
        await message.answer(
            "✅ You already have active access.\nSend a YouTube link to get started."
        )
        return

    expires_str = expires_at.strftime("%Y-%m-%d %H:%M UTC")
    await message.answer(
        "✅ Access granted for 24 hours.\nSend a YouTube link to get started."
    )

    await message.bot.send_message(  # type: ignore[union-attr]
        settings.owner_user_id,
        f"🔔 New temporary user: @{message.from_user.username} ({user_id})\n"
        f"Access granted until: {expires_str}",
    )


@router.message()
async def echo(message: Message) -> None:
    await message.answer("Bot is under construction.")
