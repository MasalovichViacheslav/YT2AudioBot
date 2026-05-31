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
        import shutil
        from pathlib import Path
        from typing import Any

        import yt_dlp

        from config.settings import settings

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "skip_download": True,
            "cachedir": False,
        }

        if settings.cookies_file:
            tmp_cookies = Path(settings.temp_dir) / "cookies.txt"
            if not tmp_cookies.exists():
                shutil.copy(settings.cookies_file, tmp_cookies)
            ydl_opts["cookiefile"] = str(tmp_cookies)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        raw_formats = info.get("formats", [])
        audio_streams = [
            f
            for f in raw_formats
            if f.get("vcodec") == "none" and f.get("abr") is not None
        ]

        service = MetadataService()
        selected = service._select_formats(raw_formats, info.get("duration", 0))

        lines = [
            f"title: {info.get('title')}",
            f"raw audio streams: {len(audio_streams)}",
            "",
        ]
        for s in audio_streams:
            lines.append(
                f"format_id={s.get('format_id')} ext={s.get('ext')} "
                f"abr={s.get('abr')} note={s.get('format_note')!r}"
            )

        lines.append("")
        lines.append(f"after _select_formats: {len(selected)}")
        for fmt in selected:
            lines.append(
                f"quality={fmt.quality} bitrate={fmt.bitrate_kbps}kbps "
                f"size={fmt.estimated_size_mb}MB format_id={fmt.format_id}"
            )

        await message.answer("\n".join(lines))
    except Exception as e:
        await message.answer(f"Error: {e}")
