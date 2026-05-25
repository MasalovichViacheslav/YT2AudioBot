from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import CancelCallback, ConfirmCallback, QualityCallback
from models.video import AudioFormat

_QUALITY_LABELS = {
    "economy": "Economy",
    "standard": "Standard",
    "high": "High",
}


def build_quality_keyboard(formats: list[AudioFormat]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fmt in formats:
        label = _QUALITY_LABELS[fmt.quality]
        builder.button(
            text=f"{label} ~{fmt.bitrate_kbps}kbps • ~{fmt.estimated_size_mb} MB",
            callback_data=QualityCallback(format_id=fmt.format_id),
        )
    builder.button(
        text="❌ Cancel",
        callback_data=CancelCallback(),
    )
    builder.adjust(1)
    return builder.as_markup()


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Yes",
        callback_data=ConfirmCallback(confirmed=True),
    )
    builder.button(
        text="❌ Cancel",
        callback_data=ConfirmCallback(confirmed=False),
    )
    builder.adjust(2)
    return builder.as_markup()


def build_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Cancel",
        callback_data=CancelCallback(),
    )
    builder.adjust(1)
    return builder.as_markup()
