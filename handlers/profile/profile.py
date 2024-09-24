import logging
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import get_session
from aiogram.dispatcher import FSMContext
from database.models import User
from config.settings import BOT_NAME
from keyboards.profile.inline import profile_menu

logger = logging.getLogger(BOT_NAME)


async def profile(message: types.Message):
    await message.delete()

    async with get_session() as session:
        session: AsyncSession
        result = await session.execute(
            select(User).filter_by(user_id=message.from_user.id).limit(1)
        )
        user = result.scalar_one_or_none()

    if user:
        await message.answer("👤 Твой профиль:", reply_markup=profile_menu())


async def close_menu(call: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.finish()
    await call.message.delete()


async def go_back_to_profile_menu(call: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.finish()
    await call.message.edit_text("👤 Твой профиль:", reply_markup=profile_menu())
