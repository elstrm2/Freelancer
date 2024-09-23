import logging
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import Dispatcher
from database.database import session
from database.models import User, BotSetting
from handlers.search.search import get_user_search_status
from keyboards.profile.reply import main_menu
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis

logger = logging.getLogger(BOT_NAME)


async def cmd_start(message: types.Message):
    await message.delete()
    user_id = message.from_user.id

    user = session.query(User).filter_by(user_id=user_id).first()

    greeting_type = "registered_user_greeting" if user else "new_user_greeting"
    greeting_cache_key = f"settings:{greeting_type}"

    cached_greeting = await redis.get(greeting_cache_key)

    if cached_greeting:
        greeting_text = (
            cached_greeting.decode("utf-8")
            if isinstance(cached_greeting, bytes)
            else cached_greeting
        )
        logger.debug(f"Приветственное сообщение для {greeting_type} загружено из кэша.")
    else:
        greeting_message = (
            session.query(BotSetting)
            .filter(getattr(BotSetting, greeting_type) != None)
            .first()
        )
        greeting_text = (
            getattr(greeting_message, greeting_type)
            if greeting_message
            else "Привет! Администратор забыл настроить registered_user_greeting или new_user_greeting."
        )
        await redis.set(greeting_cache_key, greeting_text, ex=RECORD_INTERVAL)
        logger.debug(
            f"Приветственное сообщение для {greeting_type} загружено из базы и кэшировано."
        )

    if not user:
        new_user = User(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        session.add(new_user)
        session.commit()
        logger.debug(f"Новый пользователь добавлен в базу данных: {user_id}")

    is_search_active = await get_user_search_status(user_id)
    logger.debug(f"Статус поиска для пользователя {user_id}: {is_search_active}")

    await message.answer(greeting_text, reply_markup=main_menu(is_search_active))


def register_handlers_start(dp: Dispatcher):
    dp.register_message_handler(cmd_start, Command("start"))
