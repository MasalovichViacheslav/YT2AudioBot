from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config.settings import settings
from services.invite import InviteService

router = Router()
router.message.filter(F.from_user.id == settings.owner_user_id)


@router.message(Command("enable_invite"))
async def enable_invite(message: Message, invite_service: InviteService) -> None:
    invite_service.enable()
    await message.answer("🟢 Invite access enabled.")


@router.message(Command("disable_invite"))
async def disable_invite(message: Message, invite_service: InviteService) -> None:
    invite_service.disable()
    await message.answer("🔴 Invite access disabled.")
