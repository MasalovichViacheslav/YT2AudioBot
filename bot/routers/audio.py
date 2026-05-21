import re

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.callbacks import ConfirmCallback, QualityCallback
from bot.keyboards import build_confirm_keyboard, build_quality_keyboard
from bot.states import AudioStates
from config.settings import settings
from models.video import AudioFormat, VideoMetadata
from services.invite import InviteService
from services.metadata import MetadataService, VideoUnavailableError

router = Router()

_YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+"
)


def _is_youtube_url(text: str) -> bool:
    return bool(_YOUTUBE_RE.search(text))


def _format_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _build_warning_text(fmt: AudioFormat, max_size_mb: int) -> str | None:
    is_large = fmt.estimated_size_mb > max_size_mb
    is_webm = fmt.container == "webm"

    if is_large and is_webm:
        return (
            f"⚠️ File is ~{fmt.estimated_size_mb} MB and will be uploaded "
            "to Pixeldrain.\n"
            "Also, WebM format may not play on iOS without third-party apps.\n"
            "Continue?"
        )
    if is_large:
        return (
            f"⚠️ File is ~{fmt.estimated_size_mb} MB and will be uploaded to Pixeldrain "
            "instead of sending directly to chat.\n"
            "Continue?"
        )
    if is_webm:
        return (
            "⚠️ Only WebM format is available for this video. "
            "It may not play on iOS without third-party apps.\n"
            "Continue?"
        )
    return None


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
        f"✅ Access granted until {expires_str}.\nSend a YouTube link to get started."
    )

    await message.bot.send_message(  # type: ignore[union-attr]
        settings.owner_user_id,
        f"🔔 New temporary user: @{message.from_user.username} ({user_id})\n"
        f"Access granted until: {expires_str}",
    )


@router.message(AudioStates.waiting_for_url)
async def handle_url(message: Message, state: FSMContext) -> None:
    if message.text is None:
        await message.answer(
            "I'm a bot that extracts audio from YouTube videos — not a chat bot.\n"
            "Please send a YouTube link to get started."
        )
        return

    if not _is_youtube_url(message.text):
        await message.answer(
            "That doesn't look like a YouTube link.\n"
            "Please send a valid YouTube URL, for example:\n"
            "https://youtube.com/watch?v=... or https://youtu.be/..."
        )
        return

    url = message.text
    processing_msg = await message.answer("🔍 Fetching video info...")

    try:
        metadata = MetadataService().get_metadata(url)
    except VideoUnavailableError:
        await processing_msg.edit_text(
            "❌ Video is unavailable, private, or age-restricted."
        )
        return

    await state.update_data(url=url, metadata=metadata)
    await state.set_state(AudioStates.choosing_quality)

    duration_str = _format_duration(metadata.duration_sec)
    keyboard = build_quality_keyboard(metadata.formats)
    await processing_msg.edit_text(
        f"🎵 {metadata.title} ({duration_str})\n\nChoose quality:",
        reply_markup=keyboard,
    )


@router.callback_query(QualityCallback.filter(), AudioStates.choosing_quality)
async def handle_quality_chosen(
    query: CallbackQuery, callback_data: QualityCallback, state: FSMContext
) -> None:
    await query.answer()

    if not isinstance(query.message, Message):
        return

    data = await state.get_data()
    metadata: VideoMetadata = data["metadata"]

    chosen_format = None
    for f in metadata.formats:
        if f.format_id == callback_data.format_id:
            chosen_format = f
            break

    if chosen_format is None:
        await query.message.edit_text(
            "❌ Something went wrong. Please send the link again."
        )
        await state.clear()
        return

    await state.update_data(chosen_format=chosen_format)

    warning_text = _build_warning_text(chosen_format, settings.max_file_size_mb)
    if warning_text:
        await state.set_state(AudioStates.confirming)
        await query.message.edit_text(
            warning_text, reply_markup=build_confirm_keyboard()
        )
    else:
        await state.set_state(AudioStates.downloading)
        await query.message.edit_text("⏳ Downloading...")
        await state.clear()


@router.callback_query(ConfirmCallback.filter(), AudioStates.confirming)
async def handle_confirm(
    query: CallbackQuery, callback_data: ConfirmCallback, state: FSMContext
) -> None:
    await query.answer()

    if not isinstance(query.message, Message):
        return

    if not callback_data.confirmed:
        await query.message.edit_text("❌ Cancelled.")
        await state.clear()
        return

    await state.set_state(AudioStates.downloading)
    await query.message.edit_text("⏳ Downloading...")
    await state.clear()
