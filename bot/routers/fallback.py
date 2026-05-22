from aiogram import Router
from aiogram.types import Message

from bot.states import AudioStates

router = Router()


@router.message(AudioStates.choosing_quality)
async def fallback_choosing_quality(message: Message) -> None:
    await message.answer("Please select a quality option from the menu above.")


@router.message(AudioStates.confirming)
async def fallback_confirming(message: Message) -> None:
    await message.answer("Please confirm or cancel using the buttons above.")


@router.message(AudioStates.downloading)
async def fallback_downloading(message: Message) -> None:
    await message.answer("⏳ Download in progress. Please wait until it's done.")


@router.message()
async def fallback_no_state(message: Message) -> None:
    await message.answer(
        "I'm a bot that extracts audio from YouTube videos — not a chat bot.\n"
        "Send a YouTube link to get started."
    )
