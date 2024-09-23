import logging
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from database.models import User, BotSetting
from database.database import session
from core.redis_client import redis

from config.settings import BOT_NAME, RECORD_INTERVAL

logger = logging.getLogger(BOT_NAME)


class TechWorksMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def on_pre_process_update(self, update: types.Update, data: dict):
        tech_works_status = await redis.get("settings:technical_works")

        if tech_works_status is None:
            bot_setting = session.query(BotSetting).first()
            if bot_setting:
                tech_works_status = bot_setting.technical_works
                await redis.set(
                    "settings:technical_works", tech_works_status, ex=RECORD_INTERVAL
                )
                logger.debug("Технические работы загружены из базы и сохранены в кэш.")
            else:
                tech_works_status = "0"
                await redis.set(
                    "settings:technical_works", tech_works_status, ex=RECORD_INTERVAL
                )
                logger.debug(
                    "В базе не найдено настроек, технические работы отключены по умолчанию."
                )

        if tech_works_status == "1":
            user_id = None
            if update.message:
                user_id = update.message.from_user.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id
            elif update.inline_query:
                user_id = update.inline_query.from_user.id

            if user_id is None:
                logger.debug("Технические работы активны. Обновление заблокировано.")
                raise CancelHandler()

            is_admin = await redis.get(f"user:{user_id}:is_admin")

            if is_admin is None:
                user = session.query(User).filter_by(user_id=user_id).first()
                if user:
                    is_admin = "1" if user.is_admin else "0"
                    await redis.set(
                        f"user:{user_id}:is_admin", is_admin, ex=RECORD_INTERVAL
                    )
                else:
                    is_admin = "0"
                    await redis.set(
                        f"user:{user_id}:is_admin", is_admin, ex=RECORD_INTERVAL
                    )

            if is_admin == "1":
                logger.debug(
                    f"Пользователь {user_id} является администратором. Пропускаем обновление."
                )
                return

            logger.debug(
                f"Технические работы активны. Обновление от пользователя {user_id} заблокировано."
            )
            raise CancelHandler()
