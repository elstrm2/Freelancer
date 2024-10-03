import json
import logging
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import get_session
from database.models import User, SubscriptionPlan
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from datetime import datetime
from config.settings import BOT_NAME, RECORD_INTERVAL
from core.redis_client import redis
from keyboards.profile.inline import (
    create_payment_button,
    create_subscription_plans_menu,
    subscription_menu,
)

logger = logging.getLogger(BOT_NAME)


class SelectSubscriptionStateByUser(StatesGroup):
    waiting_for_plan = State()


async def show_subscription_menu(call: types.CallbackQuery, state: FSMContext):
    if state:
        await state.finish()

    logger.debug(f"user_id from call: {call.from_user.id}")
    user_id = call.from_user.id

    subscription_end = await redis.get(f"user:{user_id}:subscription_end")

    if not subscription_end:
        async with get_session() as session:
            session: AsyncSession
            result = await session.execute(
                select(User).filter_by(user_id=user_id).limit(1)
            )
            user = result.scalar_one_or_none()

            if user and user.subscription_end:
                await redis.set(
                    f"user:{user_id}:subscription_end",
                    user.subscription_end.isoformat(),
                    ex=RECORD_INTERVAL,
                )
                subscription_end = user.subscription_end.isoformat()
                logger.debug(
                    "Дата окончания подписки пользователя загружена из базы и сохранена в кэш."
                )
            else:
                subscription_info = "❌ У тебя нет активной подписки"
                await call.message.edit_text(
                    subscription_info, reply_markup=subscription_menu(None)
                )
                return

    subscription_end_datetime = datetime.fromisoformat(subscription_end)
    if subscription_end_datetime > datetime.now():
        remaining_time = subscription_end_datetime - datetime.now()
        days, seconds = remaining_time.days, remaining_time.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        subscription_info = (
            f"✅ Твоя подписка активна!\n"
            f"♾️ Осталось: {days} дн. {hours} ч. {minutes} мин. {seconds} сек."
        )
    else:
        subscription_info = "❌ У тебя нет активной подписки"

    await call.message.edit_text(
        subscription_info,
        reply_markup=subscription_menu(subscription_end),
    )


async def show_subscription_plans(call: types.CallbackQuery, state: FSMContext):
    logger.debug(f"show_subscription_plans called for user_id: {call.from_user.id}")

    cached_plans = await redis.get("subscription_plans")

    if cached_plans:
        subscription_plans = json.loads(cached_plans)
        logger.debug("Планы подписки загружены из кэша.")
    else:
        async with get_session() as session:
            session: AsyncSession
            result = await session.execute(select(SubscriptionPlan))
            subscription_plans = result.scalars().all()

            serialized_plans = [
                {"id": plan.id, "price": plan.price, "duration": plan.duration.days}
                for plan in subscription_plans
            ]

            await redis.set(
                "subscription_plans", json.dumps(serialized_plans), ex=RECORD_INTERVAL
            )
            logger.debug("Планы подписки загружены из базы данных и сохранены в кэш.")

    await call.message.edit_text(
        "💳 Выбери план подписки:",
        reply_markup=create_subscription_plans_menu(subscription_plans),
    )

    await SelectSubscriptionStateByUser.waiting_for_plan.set()


async def select_subscription_plan(call: types.CallbackQuery, state: FSMContext):
    logger.debug(f"select_subscription_plan called with data: {call.data}")

    plan_id = int(call.data.split("_")[-1])

    async with get_session() as session:
        session: AsyncSession
        plan = await session.get(SubscriptionPlan, plan_id)

    if not plan:
        await call.message.edit_text("❌ Выбранный план не найден")
        return

    payment_message = f"💸 Тебе нужно оплатить {plan.price} рублей за {plan.duration.days} дней подписки."
    await call.message.edit_text(
        payment_message,
        reply_markup=create_payment_button(plan.price, plan.duration.days),
    )

    if state:
        await state.finish()
