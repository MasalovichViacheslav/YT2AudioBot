import asyncio
import re
import shutil
from pathlib import Path

from aiogram import Router
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger

from bot.callbacks import CancelCallback, ConfirmCallback, QualityCallback
from bot.keyboards import (
    build_cancel_keyboard,
    build_confirm_keyboard,
    build_quality_keyboard,
)
from bot.states import AudioStates
from config.settings import settings
from models.delivery import DeliveryResult
from models.video import AudioFormat, ProgressState, VideoMetadata
from services.distributor import DistributorError, DistributorService
from services.downloader import DownloadCancelledError, DownloadError, DownloaderService
from services.invite import InviteService
from services.metadata import MetadataService, VideoUnavailableError
from services.pixeldrain import PixeldrainUploadError
from services.tagger import TaggerError, TaggerService

router = Router()

_YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+"
)

_READY_MSG = "👋 Send a YouTube link and I'll extract the audio for you."


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


async def _progress_watcher(message: Message, progress_state: ProgressState) -> None:
    while not progress_state.finished and not progress_state.cancelled:
        await asyncio.sleep(2)

        if progress_state.finished or progress_state.cancelled:
            break

        filled = int(progress_state.percent / 5)
        bar = "▓" * filled + "░" * (20 - filled)
        text = (
            f"⏳ Downloading...\n\n"
            f"{bar} {progress_state.percent:.0f}%"
            f" • {progress_state.speed}"
            f" • ETA {progress_state.eta_sec}s"
        )

        try:
            await message.edit_text(text, reply_markup=build_cancel_keyboard())
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except Exception:
            pass


async def _deliver(
    message: Message,
    progress_msg: Message,
    delivery: DeliveryResult,
    title: str,
) -> None:
    if delivery.method == "telegram" and delivery.file_path is not None:
        await progress_msg.delete()
        await message.answer_audio(
            audio=FSInputFile(delivery.file_path),
            title=title,
        )
    elif delivery.method == "pixeldrain" and delivery.url is not None:
        await progress_msg.edit_text(
            f"✅ Done! File uploaded to Pixeldrain:\n{delivery.url}"
        )


async def _run_download(
    message: Message,
    state: FSMContext,
    url: str,
    chosen_format: AudioFormat,
    metadata: VideoMetadata,
) -> None:
    progress_state = ProgressState()
    await state.update_data(progress_state=progress_state)

    progress_msg = await message.answer(
        "⏳ Downloading...\n\n░░░░░░░░░░░░░░░░░░░░ 0%",
        reply_markup=build_cancel_keyboard(),
    )

    watcher_task = asyncio.create_task(_progress_watcher(progress_msg, progress_state))

    session_dir: Path | None = None
    file_path: Path | None = None

    try:
        file_path, session_dir = await DownloaderService().download(
            url, chosen_format, progress_state
        )

        TaggerService().tag(file_path, metadata.title, url)

        await progress_msg.edit_text("⬆️ Uploading...")

        delivery = await DistributorService().distribute(file_path)
        await _deliver(message, progress_msg, delivery, metadata.title)

    except DownloadCancelledError:
        pass

    except DownloadError:
        await progress_msg.edit_text("❌ Download failed. Please try again.")

    except TaggerError:
        if file_path is not None:
            logger.warning("Tagging failed, continuing without tags")
            await progress_msg.edit_text("⬆️ Uploading...")
            delivery = await DistributorService().distribute(file_path)
            await _deliver(message, progress_msg, delivery, metadata.title)

    except PixeldrainUploadError:
        await progress_msg.edit_text(
            "❌ Upload to Pixeldrain failed. Please try again."
        )

    except DistributorError:
        await progress_msg.edit_text("❌ Something went wrong. Please try again.")

    except Exception:
        logger.exception("Unexpected error during download")
        await progress_msg.edit_text("❌ Unexpected error. Please try again.")

    finally:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass

        if session_dir is not None:
            shutil.rmtree(session_dir, ignore_errors=True)

        await state.set_state(AudioStates.waiting_for_url)
        await message.answer(_READY_MSG)


@router.message(CommandStart(deep_link=True), flags={"allow_unauthorized": True})
async def start_with_token(
    message: Message, state: FSMContext, invite_service: InviteService
) -> None:
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

    await state.set_state(AudioStates.waiting_for_url)

    expires_str = expires_at.strftime("%Y-%m-%d %H:%M UTC")
    await message.answer(f"✅ Access granted until {expires_str}.\n{_READY_MSG}")

    await message.bot.send_message(  # type: ignore[union-attr]
        settings.owner_user_id,
        f"🔔 New temporary user: @{message.from_user.username} ({user_id})\n"
        f"Access granted until: {expires_str}",
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state not in (None, AudioStates.waiting_for_url):
        return
    await state.set_state(AudioStates.waiting_for_url)
    await message.answer(_READY_MSG)


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
    url: str = data["url"]

    chosen_format = None
    for f in metadata.formats:
        if f.format_id == callback_data.format_id:
            chosen_format = f
            break

    if chosen_format is None:
        await query.message.edit_text(
            "❌ Something went wrong. Please send the link again."
        )
        await state.set_state(AudioStates.waiting_for_url)
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
        await _run_download(query.message, state, url, chosen_format, metadata)


@router.callback_query(CancelCallback.filter(), AudioStates.choosing_quality)
async def handle_cancel_choosing_quality(
    query: CallbackQuery, state: FSMContext
) -> None:
    await query.answer()

    if not isinstance(query.message, Message):
        return

    await query.message.edit_text("❌ Cancelled.")
    await state.set_state(AudioStates.waiting_for_url)
    await query.message.answer(_READY_MSG)


@router.callback_query(ConfirmCallback.filter(), AudioStates.confirming)
async def handle_confirm(
    query: CallbackQuery, callback_data: ConfirmCallback, state: FSMContext
) -> None:
    await query.answer()

    if not isinstance(query.message, Message):
        return

    if not callback_data.confirmed:
        await query.message.edit_text("❌ Cancelled.")
        await state.set_state(AudioStates.waiting_for_url)
        await query.message.answer(_READY_MSG)
        return

    data = await state.get_data()
    url: str = data["url"]
    chosen_format: AudioFormat = data["chosen_format"]
    metadata: VideoMetadata = data["metadata"]

    await state.set_state(AudioStates.downloading)
    await _run_download(query.message, state, url, chosen_format, metadata)


@router.callback_query(CancelCallback.filter(), AudioStates.downloading)
async def handle_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()

    if not isinstance(query.message, Message):
        return

    data = await state.get_data()
    progress_state: ProgressState | None = data.get("progress_state")
    if progress_state is not None:
        progress_state.cancelled = True

    await query.message.edit_text("❌ Download cancelled.")
    await state.set_state(AudioStates.waiting_for_url)
    await query.message.answer(_READY_MSG)
