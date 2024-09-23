import json
import logging
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from database.database import session
from database.models import JobDirection, User, UserJobDirection
from handlers.profile.profile import close_menu
from handlers.admin.utils import paginate_items
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis
from keyboards.profile.inline import (
    create_profile_direction_menu_keyboard,
    create_profile_edit_direction_keyboard,
    create_profile_edit_job_keywords_pagination_keyboard,
    create_profile_job_directions_pagination_keyboard,
    create_profile_job_keywords_pagination_keyboard,
    create_profile_user_directions_pagination_keyboard,
)
from keyboards.shared.inline import (
    create_close_back_keyboard,
    create_confirmation_keyboard,
)

logger = logging.getLogger(BOT_NAME)


class AddUserDirectionState(StatesGroup):
    choosing_direction = State()
    selecting_keywords = State()
    waiting_for_confirmation = State()


class EditUserDirectionState(StatesGroup):
    selecting_keywords = State()
    waiting_for_confirmation = State()


class DeleteUserDirectionState(StatesGroup):
    waiting_for_confirmation = State()


async def get_all_job_directions():
    directions_cache_key = "job_directions"
    cached_directions = await redis.get(directions_cache_key)
    if cached_directions:
        job_directions = json.loads(cached_directions)
    else:
        job_directions = session.query(JobDirection).all()
        job_directions = [
            {
                "id": direction.id,
                "direction_name": direction.direction_name,
                "recommended_keywords": direction.recommended_keywords,
            }
            for direction in job_directions
        ]
        await redis.set(
            directions_cache_key, json.dumps(job_directions), ex=RECORD_INTERVAL
        )
    return job_directions


async def get_user_directions(user_id: int):
    directions_cache_key = f"user:{user_id}:directions"
    cached_directions = await redis.get(directions_cache_key)
    if cached_directions:
        user_directions = json.loads(cached_directions)
        logger.debug(f"user_directions cached: {user_directions}")
    else:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            logger.debug(f"User not found for user_id {user_id}.")
            return []

        internal_user_id = user.id
        user_directions = (
            session.query(UserJobDirection).filter_by(user_id=internal_user_id).all()
        )
        user_directions = [
            {
                "id": user_direction.id,
                "direction_id": user_direction.direction_id,
                "selected_keywords": user_direction.selected_keywords,
                "direction_name": user_direction.direction.direction_name,
            }
            for user_direction in user_directions
        ]
        logger.debug(f"user_directions cache create: {user_directions}")
        await redis.set(
            directions_cache_key, json.dumps(user_directions), ex=RECORD_INTERVAL
        )
    return user_directions


async def get_keywords_for_direction(direction_id: int):
    keywords_cache_key = f"job_direction:{direction_id}:keywords"
    cached_keywords = await redis.get(keywords_cache_key)
    if cached_keywords:
        keywords = json.loads(cached_keywords)
    else:
        direction = session.query(JobDirection).get(direction_id)
        if not direction:
            return []
        keywords = direction.recommended_keywords.split("\n")
        await redis.set(keywords_cache_key, json.dumps(keywords), ex=RECORD_INTERVAL)
    return keywords


async def paginate_directions(call: CallbackQuery, state: FSMContext = None):
    logger.debug(
        f"paginate_directions called with call.data: {call.data}, user_id: {call.from_user.id}"
    )

    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()

    user_id = call.from_user.id
    page_data = call.data.split("_")
    page = int(page_data[-1]) if len(page_data) > 2 and page_data[-1].isdigit() else 1
    limit = 6

    logger.debug(
        f"Extracting directions for user_id: {user_id}, page: {page}, limit: {limit}"
    )

    user_directions = await get_user_directions(user_id)

    start_idx = (page - 1) * limit
    page_directions = user_directions[start_idx : start_idx + limit]
    has_next = len(user_directions) > page * limit

    logger.debug(f"Total directions: {len(user_directions)}, has_next: {has_next}")
    await paginate_items(
        call=call,
        items=page_directions,
        item_name="📝 Список твоих направлений",
        keyboard_func=create_profile_user_directions_pagination_keyboard,
        keyboard_prefix="profile_directions_page",
        has_next=has_next,
    )


async def add_direction_start(call: CallbackQuery, state: FSMContext):
    logger.debug(
        f"add_direction_start called with call.data: {call.data}\nget_state: {await state.get_state()}"
    )
    job_directions = await get_all_job_directions()
    await paginate_items(
        call=call,
        items=job_directions,
        item_name="📝 Выбери направление для добавления",
        keyboard_func=create_profile_job_directions_pagination_keyboard,
        keyboard_prefix="profile_add_direction_page",
    )
    await AddUserDirectionState.choosing_direction.set()


async def select_direction(call: CallbackQuery, state: FSMContext):
    logger.debug(f"select_direction called with call.data: {call.data}")

    direction_id = int(call.data.split("_")[-1])
    logger.debug(f"Selected direction_id: {direction_id}")

    if call.data.endswith("back"):
        logger.debug("Navigating back")
        await paginate_directions(call, state)
        return
    elif call.data.endswith("close"):
        logger.debug("Closing menu")
        await close_menu(call, state)
        return

    await state.update_data(direction_id=direction_id)
    logger.debug("Setting state to AddUserDirectionState.selecting_keywords")
    await AddUserDirectionState.selecting_keywords.set()
    await paginate_keywords(call, state)


async def paginate_keywords(call: CallbackQuery, state: FSMContext):
    logger.debug(f"paginate_keywords called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = data.get("direction_id")

    keywords = await get_keywords_for_direction(direction_id)
    selected_keywords = data.get("selected_keywords", [])

    page_data = call.data.split("_")
    if len(page_data) > 3 and page_data[-1].isdigit() and page_data[-2] == "page":
        page = int(page_data[-1])
    else:
        page = data.get("current_keyword_page", 1)

    await state.update_data(current_keyword_page=page)

    logger.debug(
        f"Direction id: {direction_id}, Keywords: {keywords}, Selected keywords: {selected_keywords}, Page: {page}"
    )

    await paginate_items(
        call=call,
        items=keywords,
        item_name="🔑 Выбери ключевые слова",
        keyboard_func=lambda items, page, has_next, prefix: create_profile_job_keywords_pagination_keyboard(
            items, page, selected_keywords, has_next, prefix
        ),
        keyboard_prefix="profile_keywords_page",
        page=page,
    )


async def select_keyword(call: CallbackQuery, state: FSMContext):
    logger.debug(f"select_keyword called with call.data: {call.data}")

    selected_keywords = (await state.get_data()).get("selected_keywords", [])
    keyword = call.data.split("_")[-1]

    logger.debug(
        f"Selected keyword: {keyword}, Current selected keywords: {selected_keywords}"
    )

    logger.debug(
        f"Current redis state: {await state.get_state()}\n'keyword' arg: {keyword}"
    )

    if keyword == "back":
        logger.debug("Navigating back to add direction")
        await add_direction_start(call, state)
        return
    elif keyword == "close":
        logger.debug("Closing menu")
        await close_menu(call, state)
        return

    if keyword in selected_keywords:
        selected_keywords.remove(keyword)
        logger.debug(f"Keyword {keyword} removed from selection")
    else:
        selected_keywords.append(keyword)
        logger.debug(f"Keyword {keyword} added to selection")

    await state.update_data(selected_keywords=selected_keywords)

    data = await state.get_data()
    current_page = data.get("current_keyword_page", 1)

    logger.debug(f"Re-paginating keywords with current_page: {current_page}")

    await paginate_keywords(call, state)


async def select_all_keywords(call: CallbackQuery, state: FSMContext):
    is_editing = False

    if call.data.startswith("profile_keywords_edit_"):
        is_editing = True

    logger.debug(f"select_all_keywords called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = (
        data.get("direction_id") if not is_editing else data.get("job_direction_id")
    )
    keywords = await get_keywords_for_direction(direction_id)
    await state.update_data(selected_keywords=keywords)

    if is_editing:
        await paginate_edit_keywords(call, state)
    else:
        await paginate_keywords(call, state)


async def deselect_all_keywords(call: CallbackQuery, state: FSMContext):
    is_editing = False

    if call.data.startswith("profile_keywords_edit_"):
        is_editing = True

    logger.debug(f"deselect_all_keywords called with call.data: {call.data}")

    await state.update_data(selected_keywords=[])

    logger.debug("Все ключевые слова сняты.")

    if is_editing:
        await paginate_edit_keywords(call, state)
    else:
        await paginate_keywords(call, state)


async def confirm_add_direction(call: CallbackQuery, state: FSMContext):
    logger.debug(f"confirm_add_direction called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = data.get("direction_id")
    selected_keywords = data.get("selected_keywords", [])

    logger.debug(
        f"Confirming addition of direction {direction_id} with keywords: {selected_keywords}"
    )

    job_directions = await get_all_job_directions()
    direction = next((d for d in job_directions if d["id"] == direction_id), None)

    if not direction or not direction["recommended_keywords"] or not selected_keywords:
        logger.debug(
            "No keywords selected or direction not found, skipping confirmation"
        )
        await call.message.edit_text(
            "⚠️ Направление не найдено или ключевые слова не выбраны.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )
        return

    await call.message.edit_text(
        f"💭 Подтверди добавление направления '{direction['direction_name']}' "
        f"с {len(selected_keywords)} ключевыми словами.",
        reply_markup=create_confirmation_keyboard(
            confirm_callback="profile_confirm_add_direction_yes",
            cancel_callback="profile_confirm_add_direction_no",
        ),
    )

    await AddUserDirectionState.waiting_for_confirmation.set()
    logger.debug(f"After setting state: {await state.get_state()}")


async def add_direction_confirm(call: CallbackQuery, state: FSMContext):
    logger.debug(f"add_direction_confirm called with call.data: {call.data}")

    data = await state.get_data()

    if call.data == "profile_confirm_add_direction_yes":
        direction_id = data.get("direction_id")
        selected_keywords = data.get("selected_keywords", [])

        logger.debug(
            f"Attempting to add direction {direction_id} with selected keywords {selected_keywords}"
        )

        telegram_user_id = call.from_user.id
        user = session.query(User).filter_by(user_id=telegram_user_id).first()

        if not user:
            logger.debug(
                f"User not found in database for Telegram user_id {telegram_user_id}."
            )
            return

        internal_user_id = user.id

        existing_direction = (
            session.query(UserJobDirection)
            .filter_by(user_id=internal_user_id, direction_id=direction_id)
            .first()
        )

        if existing_direction:
            logger.debug(
                f"Direction {direction_id} already exists for user {internal_user_id}"
            )
            await call.message.edit_text(
                "⚠️ Это направление уже существует в твоем профиле.",
                reply_markup=create_close_back_keyboard("profile_directions_back"),
            )
        else:
            logger.debug(
                f"Adding new direction {direction_id} for user {internal_user_id}"
            )

            new_direction = UserJobDirection(
                user_id=internal_user_id,
                direction_id=direction_id,
                selected_keywords="\n".join(selected_keywords),
            )
            session.add(new_direction)
            session.commit()

            await redis.delete(f"user:{telegram_user_id}:directions")

            await call.message.edit_text(
                "✅ Направление успешно добавлено.",
                reply_markup=create_close_back_keyboard("profile_directions_back"),
            )

    elif call.data == "profile_confirm_add_direction_no":
        logger.debug("Addition of direction cancelled")
        await call.message.edit_text(
            "❌ Добавление направления отменено.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )

    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()


async def edit_direction(call: CallbackQuery, state: FSMContext = None):
    logger.debug(f"edit_direction called with call.data: {call.data}")

    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()

    direction_id = int(call.data.split("_")[-1])
    logger.debug(f"Selected direction_id for edit: {direction_id}")

    user_id = call.from_user.id
    user_directions = await get_user_directions(user_id)

    user_direction = next((d for d in user_directions if d["id"] == direction_id), None)
    if user_direction:
        logger.debug(f"Editing direction: {user_direction['direction_name']}")
        await call.message.edit_text(
            text=f"💭 Выбери, что редактировать в направлении '{user_direction['direction_name']}':",
            reply_markup=create_profile_edit_direction_keyboard(user_direction["id"]),
        )
    else:
        logger.debug(f"User direction {direction_id} not found.")
        await call.message.edit_text(
            f"⚠️ Направление не найдено или отсутствует в профиле",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )


async def show_direction_details(call: CallbackQuery, state: FSMContext = None):
    logger.debug(f"show_direction_details called with call.data: {call.data}")

    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()

    direction_id = int(call.data.split("_")[-1])
    logger.debug(f"Showing details for direction_id: {direction_id}")

    user_id = call.from_user.id
    user_directions = await get_user_directions(user_id)
    user_direction = next((d for d in user_directions if d["id"] == direction_id), None)

    if user_direction:
        logger.debug(
            f"Displaying details for direction: {user_direction['direction_name']}"
        )
        await call.message.edit_text(
            f"📝 Направление: {user_direction['direction_name']}\n"
            f"🔑 Количество ключевых слов: {len(user_direction['selected_keywords'].splitlines())}",
            reply_markup=create_profile_direction_menu_keyboard(user_direction["id"]),
        )
    else:
        logger.debug(f"User direction {direction_id} not found.")
        await call.message.edit_text(
            "⚠️ Направление не найдено или отсутствует в профиле",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )


async def edit_direction_keywords_start(call: CallbackQuery, state: FSMContext):
    logger.debug(f"edit_direction_keywords_start called with call.data: {call.data}")

    direction_id = int(call.data.split("_")[-1])
    logger.debug(f"Starting keyword edit for direction_id: {direction_id}")

    user_id = call.from_user.id

    user_directions = await get_user_directions(user_id)

    user_direction = next((d for d in user_directions if d["id"] == direction_id), None)

    if user_direction:
        logger.debug(
            f"Current direction keywords: {user_direction['selected_keywords']}"
        )

        keywords = await get_keywords_for_direction(user_direction["direction_id"])
        selected_keywords = user_direction["selected_keywords"].split("\n")
        logger.debug(f"Selected keywords from database: {selected_keywords}")

        page = 1
        limit = 6

        has_next = len(keywords) > limit

        await call.message.edit_text(
            f"🔑 Выбери новые ключевые слова:",
            reply_markup=create_profile_edit_job_keywords_pagination_keyboard(
                keywords=keywords[:limit],
                page=page,
                selected_keywords=selected_keywords,
                has_next=has_next,
                callback_prefix="profile_keywords_edit_page",
                direction_id=direction_id,
            ),
        )
        await EditUserDirectionState.selecting_keywords.set()
        logger.debug("State set to EditUserDirectionState.selecting_keywords")
        await state.update_data(
            direction_id=direction_id,
            job_direction_id=user_direction["direction_id"],
            current_keyword_page=page,
            selected_keywords=selected_keywords,
        )
    else:
        logger.debug(f"User direction {direction_id} not found.")
        await call.message.edit_text(
            "⚠️ Направление не найдено или отсутствует в профиле.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )


async def edit_direction_keywords(call: CallbackQuery, state: FSMContext):
    logger.debug(f"edit_direction_keywords called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = data.get("direction_id")
    user_id = call.from_user.id

    user_directions = await get_user_directions(user_id)
    user_direction = next((d for d in user_directions if d["id"] == direction_id), None)

    if not user_direction:
        logger.debug(f"User direction {direction_id} not found.")
        await call.message.edit_text(
            "⚠️ Направление не найдено или отсутствует в профиле.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )
        return

    selected_keywords = data.get("selected_keywords", [])
    keyword = call.data.split("_")[-1]

    logger.debug(
        f"Selected keyword: {keyword}, Current selected keywords: {selected_keywords}"
    )

    if keyword == "back":
        logger.debug("Navigating back to edit direction")
        await edit_direction(call, state)
        return
    elif keyword == "close":
        logger.debug("Closing menu")
        await close_menu(call, state)
        return

    if keyword in selected_keywords:
        selected_keywords.remove(keyword)
        logger.debug(f"Keyword {keyword} removed from selection")
    else:
        selected_keywords.append(keyword)
        logger.debug(f"Keyword {keyword} added to selection")

    await state.update_data(selected_keywords=selected_keywords)
    await paginate_edit_keywords(call, state)


async def confirm_edit_direction_keywords(call: CallbackQuery, state: FSMContext):
    logger.debug(f"confirm_edit_direction_keywords called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = data.get("direction_id")
    selected_keywords = data.get("selected_keywords", [])

    logger.debug(
        f"Confirming keyword change for direction_id: {direction_id} with selected keywords: {selected_keywords}"
    )

    user_id = call.from_user.id
    user_directions = await get_user_directions(user_id)
    user_direction = next((d for d in user_directions if d["id"] == direction_id), None)

    if not user_direction:
        logger.debug(f"User direction {direction_id} not found.")
        await call.message.edit_text(
            "⚠️ Направление не найдено или отсутствует в профиле.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )
        return

    await call.message.edit_text(
        f"💭 Подтверди изменение ключевых слов направления '{user_direction['direction_name']}'"
        f"на {len(selected_keywords)} ключевых слов.",
        reply_markup=create_confirmation_keyboard(
            confirm_callback="profile_confirm_edit_direction_keywords_yes",
            cancel_callback="profile_confirm_edit_direction_keywords_no",
        ),
    )
    await EditUserDirectionState.waiting_for_confirmation.set()
    logger.debug("State set to EditUserDirectionState.waiting_for_confirmation")


async def edit_direction_confirm(call: CallbackQuery, state: FSMContext):
    logger.debug(f"edit_direction_confirm called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = data.get("direction_id")

    if call.data == "profile_confirm_edit_direction_keywords_yes":
        logger.debug(f"Saving keyword changes for direction_id: {direction_id}")

        user_direction = session.query(UserJobDirection).get(direction_id)
        user_direction.selected_keywords = "\n".join(data["selected_keywords"])
        session.commit()

        directions_cache_key = f"user:{call.from_user.id}:directions"
        await redis.delete(directions_cache_key)

        logger.debug("Keywords successfully updated")
        await call.message.edit_text(
            "✅ Ключевые слова направления изменены.",
            reply_markup=create_close_back_keyboard(
                f"profile_directions_{direction_id}"
            ),
        )
    elif call.data == "profile_confirm_edit_direction_keywords_no":
        logger.debug("Keyword change cancelled")
        await call.message.edit_text(
            "❌ Изменение ключевых слов отменено.",
            reply_markup=create_close_back_keyboard(
                f"profile_directions_{direction_id}"
            ),
        )
    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()


async def confirm_delete_direction(call: CallbackQuery):
    logger.debug(f"confirm_delete_direction called with call.data: {call.data}")

    direction_id = int(call.data.split("_")[-1])
    user_id = call.from_user.id

    user_directions = await get_user_directions(user_id)

    user_direction = next((d for d in user_directions if d["id"] == direction_id), None)

    if not user_direction:
        logger.debug(f"User direction {direction_id} not found.")
        await call.message.edit_text(
            "⚠️ Направление не найдено или отсутствует в профиле.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )
        return

    logger.debug(
        f"Confirming deletion of direction: {user_direction['direction_name']}"
    )

    await call.message.edit_text(
        f"💭 Ты уверен, что хочешь удалить направление '{user_direction['direction_name']}'?",
        reply_markup=create_confirmation_keyboard(
            confirm_callback=f"profile_confirm_delete_direction_{direction_id}",
            cancel_callback=f"profile_cancel_delete_direction_{direction_id}",
        ),
    )

    await DeleteUserDirectionState.waiting_for_confirmation.set()
    logger.debug("State set to DeleteUserDirectionState.waiting_for_confirmation")


async def delete_direction(call: CallbackQuery, state: FSMContext):
    logger.debug(f"delete_direction called with call.data: {call.data}")

    direction_id = int(call.data.split("_")[-1])
    user_direction = session.query(UserJobDirection).get(direction_id)

    if user_direction:
        logger.debug(f"Deleting direction: {user_direction.direction.direction_name}")
        session.delete(user_direction)
        session.commit()

        user_id = call.from_user.id
        directions_cache_key = f"user:{user_id}:directions"
        keywords_cache_key = f"job_direction:{user_direction.direction_id}:keywords"
        await redis.delete(directions_cache_key)
        await redis.delete(keywords_cache_key)

        await call.message.edit_text(
            f"🗑️ Направление '{user_direction.direction.direction_name}' было удалено.",
            reply_markup=create_close_back_keyboard(f"profile_directions_back"),
        )
    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()


async def cancel_delete_direction(call: CallbackQuery, state: FSMContext):
    logger.debug(f"cancel_delete_direction called with call.data: {call.data}")
    direction_id = int(call.data.split("_")[-1])

    await call.message.edit_text(
        "❌ Удаление направления отменено.",
        reply_markup=create_close_back_keyboard(f"profile_directions_{direction_id}"),
    )
    if state:
        logger.debug("Finishing current FSM state")
        await state.finish()


async def edit_select_keyword(call: CallbackQuery, state: FSMContext):
    logger.debug(f"edit_select_keyword called with call.data: {call.data}")

    selected_keywords = (await state.get_data()).get("selected_keywords", [])
    keyword = call.data.split("_")[-1]

    logger.debug(
        f"Selected keyword: {keyword}, Current selected keywords: {selected_keywords}"
    )

    if keyword in selected_keywords:
        selected_keywords.remove(keyword)
        logger.debug(f"Keyword {keyword} removed from selection")
    else:
        selected_keywords.append(keyword)
        logger.debug(f"Keyword {keyword} added to selection")

    await state.update_data(selected_keywords=selected_keywords)

    await paginate_edit_keywords(call, state)


async def paginate_edit_keywords(call: CallbackQuery, state: FSMContext):
    logger.debug(f"paginate_edit_keywords called with call.data: {call.data}")

    data = await state.get_data()
    direction_id = data.get("direction_id")
    job_direction_id = data.get("job_direction_id")

    all_directions = await get_all_job_directions()

    direction = next((d for d in all_directions if d["id"] == job_direction_id), None)

    if not direction:
        logger.debug(f"JobDirection с id {job_direction_id} не найден.")
        await call.message.edit_text(
            "⚠️ Направление не найдено или отсутствует в системе.",
            reply_markup=create_close_back_keyboard("profile_directions_back"),
        )
        return

    keywords = await get_keywords_for_direction(direction["id"])

    selected_keywords = data.get("selected_keywords", [])

    filtered_selected_keywords = [
        keyword for keyword in selected_keywords if keyword in keywords
    ]

    await state.update_data(selected_keywords=filtered_selected_keywords)

    page_data = call.data.split("_")
    if len(page_data) > 3 and page_data[-2] == "page" and page_data[-1].isdigit():
        page = int(page_data[-1])
    else:
        page = data.get("current_keyword_page", 1)

    await state.update_data(current_keyword_page=page)

    logger.debug(
        f"Direction id: {direction_id}, Job Direction id: {job_direction_id}, Keywords: {keywords}, Filtered selected keywords: {filtered_selected_keywords}, Page: {page}"
    )

    limit = 6
    start_idx = (page - 1) * limit
    page_keywords = keywords[start_idx : start_idx + limit]
    has_next = len(keywords) > page * limit

    await call.message.edit_text(
        "🔑 Выбери новые ключевые слова:",
        reply_markup=create_profile_edit_job_keywords_pagination_keyboard(
            keywords=page_keywords,
            page=page,
            selected_keywords=filtered_selected_keywords,
            has_next=has_next,
            callback_prefix="profile_keywords_edit_page",
            direction_id=direction_id,
        ),
    )
