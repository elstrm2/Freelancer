from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(is_search_active: bool) -> ReplyKeyboardMarkup:
    keyboard = []

    if is_search_active:
        keyboard.append([KeyboardButton(text="❌ Прекратить поиск")])
    else:
        keyboard.append([KeyboardButton(text="🔍 Начать поиск")])

    keyboard.append([KeyboardButton(text="👤 Мой профиль")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
