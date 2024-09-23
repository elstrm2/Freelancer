from aiogram import Dispatcher
from .profile import *
from .subscription import *
from .support import *
from .promocodes import *
from .directions import *


def register_handlers_profile(dp: Dispatcher):
    # --- Команда "👤 Мой профиль" ---
    dp.register_message_handler(
        profile,
        lambda message: message.text == "👤 Мой профиль",
    )

    # --- Хэндлеры для подписки ---
    dp.register_callback_query_handler(
        show_subscription_menu,
        lambda call: call.data == "profile_subscription",
        state="*",
    )
    dp.register_callback_query_handler(
        show_subscription_plans,
        lambda call: call.data == "buy_subscription",
    )
    dp.register_callback_query_handler(
        select_subscription_plan,
        lambda call: call.data.startswith("select_subscription_plan_"),
        state=SelectSubscriptionStateByUser.waiting_for_plan,
    )

    # --- Хэндлеры для поддержки ---
    dp.register_callback_query_handler(
        user_support, lambda call: call.data == "profile_support"
    )

    # --- Хэндлеры для промокодов ---
    dp.register_callback_query_handler(
        enter_promo_code_start, lambda call: call.data == "profile_promo_codes"
    )
    dp.register_message_handler(
        enter_promo_code, state=EnterPromoCodeState.waiting_for_code
    )
    dp.register_callback_query_handler(
        confirm_promo_code, state=EnterPromoCodeState.waiting_for_confirmation
    )

    # --- Хэндлеры для направлений ---
    dp.register_callback_query_handler(
        paginate_directions,
        lambda call: call.data.startswith("profile_directions_page"),
    )
    dp.register_callback_query_handler(
        add_direction_start,
        lambda call: call.data.startswith("profile_add_direction_page"),
        state="*",  # иначе пагинация сломается
    )
    dp.register_callback_query_handler(
        select_direction,
        lambda call: call.data.startswith("profile_add_direction_")
        and not call.data.startswith("profile_add_direction_page"),
        state=AddUserDirectionState.choosing_direction,
    )

    # Хэндлеры для пагинации при добавлении
    dp.register_callback_query_handler(
        paginate_keywords,
        lambda call: call.data.startswith("profile_keywords_page")
        and not call.data.startswith("profile_keywords_page_confirm")
        and not call.data.endswith("select_all")
        and not call.data.endswith(
            "cancel_all"
        ),  # чтобы кнопка продолжала работала, а также работал select/deselect
        state=AddUserDirectionState.selecting_keywords,
    )

    # Хэндлер для выбора отдельного ключевого слова при добавлении
    dp.register_callback_query_handler(
        select_keyword,
        lambda call: call.data.startswith("profile_add_keyword_"),
        state=AddUserDirectionState.selecting_keywords,
    )
    dp.register_callback_query_handler(
        confirm_add_direction,
        lambda call: call.data == "profile_keywords_page_confirm",
        state=AddUserDirectionState.selecting_keywords,
    )
    dp.register_callback_query_handler(
        add_direction_confirm,
        lambda call: call.data.startswith("profile_confirm_add_direction_"),
        state=AddUserDirectionState.waiting_for_confirmation,
    )

    # --- Хэндлеры для выбора и отмены выбора всех ключевых слов ---
    # Для добавления ключевых слов
    dp.register_callback_query_handler(
        select_all_keywords,
        lambda c: c.data.endswith("select_all"),
        state=AddUserDirectionState.selecting_keywords,
    )
    dp.register_callback_query_handler(
        deselect_all_keywords,
        lambda c: c.data.endswith("cancel_all"),
        state=AddUserDirectionState.selecting_keywords,
    )

    # Для редактирования ключевых слов
    dp.register_callback_query_handler(
        select_all_keywords,
        lambda c: c.data.endswith("select_all"),
        state=EditUserDirectionState.selecting_keywords,
    )
    dp.register_callback_query_handler(
        deselect_all_keywords,
        lambda c: c.data.endswith("cancel_all"),
        state=EditUserDirectionState.selecting_keywords,
    )

    # --- Хэндлеры для редактирования направлений ---
    dp.register_callback_query_handler(
        show_direction_details,
        lambda call: call.data.startswith("profile_directions_")
        and not call.data.startswith("profile_directions_back"),
    )
    dp.register_callback_query_handler(
        edit_direction,
        lambda call: call.data.startswith("profile_edit_direction_")
        and not call.data.startswith("profile_edit_direction_name_")
        and not call.data.startswith("profile_edit_direction_keywords_"),
        state="*",  # чтобы выход из редактирования переменной работал
    )
    dp.register_callback_query_handler(
        edit_direction_keywords_start,
        lambda call: call.data.startswith("profile_edit_direction_keywords_"),
        state="*",
    )
    dp.register_callback_query_handler(
        edit_direction_keywords,
        lambda call: call.data.startswith("profile_keywords_edit_")
        and not call.data.startswith("profile_keywords_edit_page_"),
        state=EditUserDirectionState.selecting_keywords,
    )
    dp.register_callback_query_handler(
        confirm_edit_direction_keywords,
        lambda call: call.data == "profile_keywords_edit_page_confirm",
        state=EditUserDirectionState.selecting_keywords,
    )
    dp.register_callback_query_handler(
        edit_direction_confirm,
        lambda call: call.data.startswith("profile_confirm_edit_direction_keywords_"),
        state=EditUserDirectionState.waiting_for_confirmation,
    )

    # Хэндлер для выбора отдельного ключевого слова при редактировании
    dp.register_callback_query_handler(
        edit_select_keyword,
        lambda call: call.data.startswith("profile_edit_keyword_"),
        state=EditUserDirectionState.selecting_keywords,
    )

    # Хэндлеры для пагинации при редактировании
    dp.register_callback_query_handler(
        paginate_edit_keywords,
        lambda call: call.data.startswith("profile_keywords_edit_page_")
        and not call.data == "profile_keywords_edit_page_confirm",
        state=EditUserDirectionState.selecting_keywords,
    )

    # --- Хэндлеры для удаления направлений ---
    dp.register_callback_query_handler(
        confirm_delete_direction,
        lambda call: call.data.startswith("profile_confirm_delete_direction_"),
    )
    dp.register_callback_query_handler(
        cancel_delete_direction,
        lambda call: call.data.startswith("profile_cancel_delete_direction_"),
        state=DeleteUserDirectionState.waiting_for_confirmation,
    )
    dp.register_callback_query_handler(
        delete_direction,
        lambda call: call.data.startswith("profile_confirm_delete_direction_"),
        state=DeleteUserDirectionState.waiting_for_confirmation,
    )

    # --- Хэндлеры для возврата ---
    dp.register_callback_query_handler(
        go_back_to_profile_menu, text="profile_back", state="*"
    )
    dp.register_callback_query_handler(
        paginate_directions, text="profile_directions_back", state="*"
    )

    # --- Закрытие меню ---
    dp.register_callback_query_handler(close_menu, text="close", state="*")
