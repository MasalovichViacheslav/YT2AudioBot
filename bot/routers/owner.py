from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config.settings import settings
from services.invite import InviteService
from services.metadata import MetadataService

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


@router.message(Command("debug_url"))
async def debug_url(message: Message) -> None:
    if message.text is None:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /debug_url <youtube_url>")
        return

    url = parts[1]
    try:
        metadata = MetadataService().get_metadata(url)
        lines = [f"title: {metadata.title}", f"duration: {metadata.duration_sec}s", ""]
        for fmt in metadata.formats:
            lines.append(
                f"quality={fmt.quality} bitrate={fmt.bitrate_kbps}kbps "
                f"size={fmt.estimated_size_mb}MB format_id={fmt.format_id}"
            )
        await message.answer("\n".join(lines))
    except Exception as e:
        await message.answer(f"Error: {e}")
