from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import BOT_NAME
import logging

logger = logging.getLogger(BOT_NAME)


def create_close_keyboard():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close")
    )


def create_close_back_keyboard(back_callback_data: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад", callback_data=back_callback_data
        ),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
    )
    return keyboard


def create_confirmation_keyboard(
    confirm_callback: str, cancel_callback: str
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="✅ Да", callback_data=confirm_callback),
        InlineKeyboardButton(text="❌ Нет", callback_data=cancel_callback),
    )
    return keyboard
