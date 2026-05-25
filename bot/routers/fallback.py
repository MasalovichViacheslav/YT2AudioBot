from aiogram import Router
from aiogram.types import Message

from bot.states import AudioStates

router = Router()


@router.message(AudioStates.choosing_quality)
async def fallback_choosing_quality(message: Message) -> None:
    await message.answer("Please select a quality option or press ❌ Cancel.")


@router.message(AudioStates.confirming)
async def fallback_confirming(message: Message) -> None:
    await message.answer("Please confirm or press ❌ Cancel.")


@router.message(AudioStates.downloading)
async def fallback_downloading(message: Message) -> None:
    await message.answer("⏳ Download in progress. Please wait or press ❌ Cancel.")
