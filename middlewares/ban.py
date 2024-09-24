import logging
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import get_session
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis

logger = logging.getLogger(BOT_NAME)


class BanMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        user_id = None

        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        elif update.inline_query:
            user_id = update.inline_query.from_user.id

        if user_id is None:
            return

        cache_key = f"user:{user_id}:is_banned"
        is_banned = await redis.get(cache_key)

        if is_banned is not None:
            is_banned = (
                is_banned.decode("utf-8") == "true"
                if isinstance(is_banned, bytes)
                else is_banned == "true"
            )
            logger.debug(
                f"Ban status for user {user_id} loaded from cache: {is_banned}"
            )
        else:
            async with get_session() as session:
                session: AsyncSession
                result = await session.execute(
                    select(User).filter_by(user_id=user_id).limit(1)
                )
                user = result.scalar_one_or_none()
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
