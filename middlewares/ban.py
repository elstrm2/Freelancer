import logging
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from database.models import User
from database.database import session
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis

logger = logging.getLogger(BOT_NAME)


class BanMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        elif update.inline_query:
            user_id = update.inline_query.from_user.id
        else:
            return

        cache_key = f"user:{user_id}:is_banned"

        is_banned = await redis.get(cache_key)

        if is_banned is not None:
            is_banned = is_banned == "true"
            logger.debug(
                f"Ban status for user {user_id} loaded from cache: {is_banned}"
            )
        else:
            user = session.query(User).filter_by(user_id=user_id).first()
            is_banned = user.is_banned if user else False

            await redis.set(cache_key, str(is_banned).lower(), ex=RECORD_INTERVAL)
            logger.debug(
                f"Ban status for user {user_id} loaded from database and cached: {is_banned}"
            )

        if is_banned:
            logger.debug(
                f"Пользователь {user_id} в бане пытался взаимодействовать с ботом."
            )
            raise CancelHandler()
