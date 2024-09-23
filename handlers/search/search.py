import logging
import json
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.database import session
from keyboards.admin.inline import create_close_keyboard
from database.models import User, UserJobDirection
from datetime import datetime
from keyboards.profile.reply import main_menu
from config.settings import BOT_NAME, RECORD_INTERVAL, SHORT_RECORD_INTERVAL
from core.redis_client import redis

logger = logging.getLogger(BOT_NAME)


def get_user_subscription_key(user_id):
    return f"user:{user_id}:subscription_end"


def get_user_directions_key(user_id):
    return f"user:{user_id}:directions"


def get_user_search_key(user_id):
    return f"user:{user_id}:is_search_active"


async def get_user_subscription_end(user_id):
    subscription_key = get_user_subscription_key(user_id)
    subscription_end = await redis.get(subscription_key)

    if subscription_end:
        subscription_end = (
            subscription_end.decode("utf-8")
            if isinstance(subscription_end, bytes)
            else subscription_end
        )
    else:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user and user.subscription_end:
            subscription_end = user.subscription_end.isoformat()
            await redis.set(subscription_key, subscription_end, ex=RECORD_INTERVAL)
            logger.debug(
                f"Дата окончания подписки загружена из базы и сохранена в кэш для пользователя {user_id}."
            )
        else:
            subscription_end = None

    return subscription_end


async def get_user_directions(user_id):
    directions_key = get_user_directions_key(user_id)
    cached_directions = await redis.get(directions_key)

    if cached_directions:
        user_directions = json.loads(
            cached_directions.decode("utf-8")
            if isinstance(cached_directions, bytes)
            else cached_directions
        )
        logger.debug(f"Направления пользователя {user_id} загружены из кэша.")
    else:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            logger.debug(f"Пользователь с user_id {user_id} не найден.")
            return []

        internal_user_id = user.id

        user_directions = (
            session.query(UserJobDirection).filter_by(user_id=internal_user_id).all()
        )

        user_directions = [
            {
                "id": direction.id,
                "direction_id": direction.direction_id,
                "selected_keywords": direction.selected_keywords,
                "direction_name": direction.direction.direction_name,
            }
            for direction in user_directions
        ]

        if user_directions:
            await redis.set(
                directions_key, json.dumps(user_directions), ex=RECORD_INTERVAL
            )
            logger.debug(
                f"Направления пользователя {user_id} загружены из базы и сохранены в кэш."
            )
        else:
            user_directions = []

    return user_directions


async def get_user_search_status(user_id):
    search_key = get_user_search_key(user_id)
    is_search_active = await redis.get(search_key)

    if is_search_active:
        is_search_active = (
            is_search_active.decode("utf-8")
            if isinstance(is_search_active, bytes)
            else is_search_active
        )
        logger.debug(
            f"Статус поиска для пользователя {user_id} загружен из кэша: {is_search_active}"
        )
    else:
        is_search_active = "0"
        logger.debug(
            f"Статус поиска для пользователя {user_id} не найден в кэше, устанавливается значение по умолчанию: {is_search_active}"
        )

    if is_search_active == "1":
        await redis.expire(search_key, SHORT_RECORD_INTERVAL)
        logger.debug(
            f"TTL для статуса поиска пользователя {user_id} обновлен на {SHORT_RECORD_INTERVAL} секунд."
        )

    return is_search_active == "1"


async def cmd_start_search(message: types.Message):
    await message.delete()
    user_id = message.from_user.id

    subscription_end = await get_user_subscription_end(user_id)
    if (
        not subscription_end
        or datetime.fromisoformat(subscription_end) < datetime.now()
    ):
        await message.answer(
            "⚠️ У тебя нет активной подписки.", reply_markup=create_close_keyboard()
        )
        logger.debug(
            f"Попытка начать поиск пользователем {user_id} без активной подписки."
        )
        return

    user_directions = await get_user_directions(user_id)
    if not user_directions:
        await message.answer(
            "⚠️ Ты не выбрал ни одного направления для поиска.",
            reply_markup=create_close_keyboard(),
        )
        logger.debug(
            f"Пользователь {user_id} попытался начать поиск без выбранных направлений."
        )
        return

    search_key = get_user_search_key(user_id)
    await redis.set(search_key, "1", ex=RECORD_INTERVAL)
    logger.debug(f"Поиск для пользователя {user_id} начат и статус кэширован в Redis.")

    await message.answer(
        "🔍 Поиск начат!",
        reply_markup=main_menu(True),
    )


async def cmd_stop_search(message: types.Message):
    await message.delete()
    user_id = message.from_user.id

    search_key = get_user_search_key(user_id)
    await redis.delete(search_key)
    logger.debug(
        f"Поиск для пользователя {user_id} остановлен и статус удалён из Redis."
    )

    await message.answer(
        "❌ Поиск прекращен.",
        reply_markup=main_menu(False),
    )


def register_handlers_search(dp: Dispatcher):
    dp.register_message_handler(
        cmd_start_search, lambda message: message.text == "🔍 Начать поиск"
    )
    dp.register_message_handler(
        cmd_stop_search, lambda message: message.text == "❌ Прекратить поиск"
    )
