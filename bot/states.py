from aiogram.fsm.state import State, StatesGroup


class AudioStates(StatesGroup):
    waiting_for_url = State()
    choosing_quality = State()
    confirming = State()
    downloading = State()
