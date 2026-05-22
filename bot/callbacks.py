from aiogram.filters.callback_data import CallbackData


class QualityCallback(CallbackData, prefix="quality"):
    format_id: str


class ConfirmCallback(CallbackData, prefix="confirm"):
    confirmed: bool


class CancelCallback(CallbackData, prefix="cancel"):
    pass
