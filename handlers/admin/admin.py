import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import get_session
from database.models import User
from keyboards.admin.inline import admin_menu
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis

logger = logging.getLogger(BOT_NAME)


async def admin(message: types.Message) -> None:
    user_id = message.from_user.id
    is_admin = await redis.get(f"user:{user_id}:is_admin")

    if is_admin is None:
        async with get_session() as session:
            session: AsyncSession
            result = await session.execute(
                select(User).filter_by(user_id=user_id, is_admin=True).limit(1)
            )
            user = result.scalar_one_or_none()

            if user:
                is_admin = "1"
                await redis.set(
                    f"user:{user_id}:is_admin", is_admin, ex=RECORD_INTERVAL
                )
                logger.debug(
                    f"Пользователь {user_id} добавлен в Redis как администратор."
                )
            else:
                is_admin = "0"
                await redis.set(
                    f"user:{user_id}:is_admin", is_admin, ex=RECORD_INTERVAL
                )
                logger.debug(
                    f"Пользователь {user_id} добавлен в Redis как не администратор."
                )

    if is_admin == "1":
        await message.delete()
        await message.answer("👑 Админ-меню:", reply_markup=admin_menu())


async def close_menu(call: types.CallbackQuery, state: FSMContext = None) -> None:
    if state:
        await state.finish()
    await call.message.delete()


async def go_back_to_admin_menu(
    call: types.CallbackQuery, state: FSMContext = None
) -> None:
    if state:
        await state.finish()
    await call.message.edit_text("👑 Админ-меню:", reply_markup=admin_menu())
