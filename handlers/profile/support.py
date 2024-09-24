import logging
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import get_session
from database.models import BotSetting
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis
from keyboards.shared.inline import create_close_back_keyboard

logger = logging.getLogger(BOT_NAME)


async def user_support(call: types.CallbackQuery):
    cache_key = "settings:support_message"

    support_message = await redis.get(cache_key)

    if not support_message:
        async with get_session() as session:
            session: AsyncSession
            result = await session.execute(select(BotSetting).limit(1))
            support_message_setting = result.scalar_one_or_none()

            if support_message_setting and support_message_setting.support_message:
                support_message = support_message_setting.support_message
                await redis.set(cache_key, support_message, ex=RECORD_INTERVAL)
                logger.debug(
                    "Сообщение поддержки загружено из базы данных и сохранено в кэш."
                )

    if support_message:
        await call.message.edit_text(
            support_message, reply_markup=create_close_back_keyboard("profile_back")
        )
