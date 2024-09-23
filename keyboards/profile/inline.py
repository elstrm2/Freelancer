from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import BOT_NAME
import logging

logger = logging.getLogger(BOT_NAME)


def profile_menu():
    buttons = [
        InlineKeyboardButton(text="❓ Поддержка", callback_data="profile_support"),
        InlineKeyboardButton(text="🎫 Промокоды", callback_data="profile_promo_codes"),
        InlineKeyboardButton(
            text="📝 Направления", callback_data="profile_directions_page"
        ),
        InlineKeyboardButton(text="⭐ Подписка", callback_data="profile_subscription"),
    ]

    buttons.append(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))
    return InlineKeyboardMarkup(row_width=2).add(*buttons)


def subscription_menu(subscription_end: str) -> InlineKeyboardMarkup:
    buttons = []

    if subscription_end:
        subscription_end_datetime = datetime.fromisoformat(subscription_end)
        if subscription_end_datetime < datetime.now():
            buttons.append(
                InlineKeyboardButton(
                    text="🎯 Купить подписку", callback_data="buy_subscription"
                )
            )
    else:
        buttons.append(
            InlineKeyboardButton(
                text="🎯 Купить подписку", callback_data="buy_subscription"
            )
        )

    buttons.append(
        InlineKeyboardButton(text="↩️ Вернуться назад", callback_data="profile_back")
    )
    buttons.append(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))

    return InlineKeyboardMarkup(row_width=2).add(*buttons)


def create_profile_direction_menu_keyboard(direction_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ Редактировать направление",
            callback_data=f"profile_edit_direction_{direction_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🗑️ Удалить направление",
            callback_data=f"profile_confirm_delete_direction_{direction_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад", callback_data="profile_directions_back"
        )
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))

    return keyboard


def create_profile_job_directions_pagination_keyboard(
    directions, page, has_next, callback_prefix
):
    keyboard = InlineKeyboardMarkup()

    for direction in directions:
        item_text = f"📝 {direction['direction_name']}"
        keyboard.add(
            InlineKeyboardButton(
                item_text, callback_data=f"profile_add_direction_{direction['id']}"
            )
        )

    if has_next:
        keyboard.add(
            InlineKeyboardButton(
                "➡️ Вперед", callback_data=f"{callback_prefix}_{page+1}"
            )
        )
    if page > 1:
        keyboard.add(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{callback_prefix}_{page-1}")
        )

    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад", callback_data="profile_directions_back"
        )
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))
    return keyboard


def create_profile_user_directions_pagination_keyboard(
    directions, page, has_next, callback_prefix
):
    keyboard = InlineKeyboardMarkup()

    for user_direction in directions:
        item_text = f"📝 {user_direction['direction_name']}"
        keyboard.add(
            InlineKeyboardButton(
                item_text, callback_data=f"profile_directions_{user_direction['id']}"
            )
        )

    if has_next:
        keyboard.add(
            InlineKeyboardButton(
                "➡️ Вперед", callback_data=f"{callback_prefix}_{page+1}"
            )
        )
    if page > 1:
        keyboard.add(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{callback_prefix}_{page-1}")
        )

    keyboard.add(
        InlineKeyboardButton(
            "➕ Добавить направление", callback_data="profile_add_direction_page"
        )
    )

    keyboard.add(
        InlineKeyboardButton(text="↩️ Вернуться назад", callback_data="profile_back")
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))
    return keyboard


def create_profile_edit_job_keywords_pagination_keyboard(
    keywords, page, selected_keywords, has_next, callback_prefix, direction_id
):
    keyboard = InlineKeyboardMarkup()
    logger.debug(f"Creating keyboard for page {page} with keywords: {keywords}")

    for keyword in keywords:
        item_text = f"📌 {keyword}" if keyword in selected_keywords else keyword
        callback_data = f"profile_edit_keyword_{keyword}"
        keyboard.add(InlineKeyboardButton(item_text, callback_data=callback_data))
        logger.debug(f"Added button: {item_text} with callback_data: {callback_data}")

    if has_next:
        keyboard.add(
            InlineKeyboardButton(
                "➡️ Вперед", callback_data=f"{callback_prefix}_{page+1}"
            )
        )
    if page > 1:
        keyboard.add(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{callback_prefix}_{page-1}")
        )

    keyboard.add(
        InlineKeyboardButton(
            text="📋 Выбрать все", callback_data=f"{callback_prefix}_select_all"
        ),
        InlineKeyboardButton(
            text="🧹 Снять выбор всех",
            callback_data=f"{callback_prefix}_cancel_all",
        ),
    )

    if selected_keywords:
        keyboard.add(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data=f"{callback_prefix}_confirm"
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад",
            callback_data=f"profile_edit_direction_{direction_id}",
        )
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))
    return keyboard


def create_profile_job_keywords_pagination_keyboard(
    keywords, page, selected_keywords, has_next, callback_prefix
):
    keyboard = InlineKeyboardMarkup()

    for keyword in keywords:
        item_text = f"📌 {keyword}" if keyword in selected_keywords else keyword
        keyboard.add(
            InlineKeyboardButton(
                item_text, callback_data=f"profile_add_keyword_{keyword}"
            )
        )

    if has_next:
        keyboard.add(
            InlineKeyboardButton(
                "➡️ Вперед", callback_data=f"{callback_prefix}_{page+1}"
            )
        )
    if page > 1:
        keyboard.add(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{callback_prefix}_{page-1}")
        )

    keyboard.add(
        InlineKeyboardButton(
            text="📋 Выбрать все", callback_data=f"{callback_prefix}_select_all"
        ),
        InlineKeyboardButton(
            text="🧹 Снять выбор всех",
            callback_data=f"{callback_prefix}_cancel_all",
        ),
    )

    if selected_keywords:
        keyboard.add(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data=f"{callback_prefix}_confirm"
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад", callback_data="profile_directions_back"
        )
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))
    return keyboard


def create_profile_edit_direction_keyboard(direction_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🔑 Редактировать ключевые слова",
            callback_data=f"profile_edit_direction_keywords_{direction_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад", callback_data=f"profile_directions_{direction_id}"
        )
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))

    return keyboard


def create_subscription_plans_menu(subscription_plans):
    keyboard = InlineKeyboardMarkup()

    for plan in subscription_plans:
        button_text = f"⭐️ {plan.price} руб. за {plan.duration.days} дней"
        callback_data = f"select_subscription_plan_{plan.id}"
        keyboard.add(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )

    keyboard.add(
        InlineKeyboardButton(
            text="↩️ Вернуться назад", callback_data="profile_subscription"
        )
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))

    return keyboard


def create_payment_button(price, days):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="✨ Перейти на страницу оплаты", url="https://google.com"
        )
    )
    keyboard.add(
        InlineKeyboardButton(text="↩️ Вернуться назад", callback_data="buy_subscription")
    )
    keyboard.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close"))

    return keyboard
