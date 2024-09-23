import logging
from datetime import timedelta, datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config.settings import BOT_NAME, RECORD_INTERVAL
from database.database import session
from database.models import PromoCode, PromoCodeUsage, User
from core.redis_client import redis
from keyboards.shared.inline import (
    create_close_back_keyboard,
    create_confirmation_keyboard,
)

logger = logging.getLogger(BOT_NAME)


class EnterPromoCodeState(StatesGroup):
    waiting_for_code = State()
    waiting_for_confirmation = State()


async def enter_promo_code_start(call: types.CallbackQuery, state: FSMContext):
    sent_message = await call.message.edit_text(
        "🎫 Введи промокод:",
        reply_markup=create_close_back_keyboard("profile_back"),
    )
    await EnterPromoCodeState.waiting_for_code.set()
    await state.update_data(message_id=sent_message.message_id, retry_count=0)


async def enter_promo_code(message: types.Message, state: FSMContext):
    await message.delete()

    promo_code_input = message.text.strip()
    user_id = message.from_user.id
    retry_count = (await state.get_data()).get("retry_count", 0)
    message_id = (await state.get_data()).get("message_id")

    promo_code_key = f"promo_code:{promo_code_input}"
    promo_code = await redis.hgetall(promo_code_key)

    if not promo_code:
        promo_code = session.query(PromoCode).filter_by(code=promo_code_input).first()
        if promo_code:
            promo_code = {
                "id": promo_code.id,
                "name": promo_code.name,
                "max_uses": promo_code.max_uses,
                "promo_type": promo_code.promo_type,
                "value": promo_code.value,
            }
            await redis.hset(promo_code_key, mapping=promo_code)
            await redis.expire(promo_code_key, RECORD_INTERVAL)
            logger.debug("Промокод загружен из базы и сохранен в кэш.")
        else:
            retry_count += 1
            await state.update_data(retry_count=retry_count)
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message_id,
                text=f"⚠️ Промокод не найден. Попытка {retry_count}. Попробуй ещё раз:",
                reply_markup=create_close_back_keyboard("profile_back"),
            )
            await EnterPromoCodeState.waiting_for_code.set()
            return

    usage_count_key = f"promo_code:{promo_code['id']}:usage_count"
    usage_count = await redis.get(usage_count_key)

    if usage_count is None:
        usage_count = (
            session.query(PromoCodeUsage)
            .filter_by(promo_code_id=promo_code["id"])
            .count()
        )
        await redis.set(usage_count_key, usage_count, ex=RECORD_INTERVAL)

    if int(usage_count) >= int(promo_code["max_uses"]):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text="⚠️ Промокод уже достиг максимального количества использований.",
            reply_markup=create_close_back_keyboard("profile_back"),
        )
        if state:
            await state.finish()
        return

    await state.update_data(promo_code_id=promo_code["id"])
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=f"💭 Промокод найден: {promo_code['name']}. Применить его?",
        reply_markup=create_confirmation_keyboard(
            confirm_callback="confirm_promo_code_yes",
            cancel_callback="confirm_promo_code_no",
        ),
    )
    await EnterPromoCodeState.waiting_for_confirmation.set()


async def confirm_promo_code(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    promo_code_id = data["promo_code_id"]
    user_id = call.from_user.id
    promo_code = session.query(PromoCode).get(promo_code_id)
    user = session.query(User).filter_by(user_id=user_id).first()

    user_usage_key = f"user:{user_id}:promo_code_usage:{promo_code_id}"
    user_usage = await redis.get(user_usage_key)

    if user_usage is None:
        user_usage = (
            session.query(PromoCodeUsage)
            .filter_by(user_id=user.id, promo_code_id=promo_code.id)
            .first()
        )
        if user_usage:
            await redis.set(user_usage_key, "1", ex=RECORD_INTERVAL)
            await call.message.edit_text(
                "⚠️ Ты уже использовал этот промокод.",
                reply_markup=create_close_back_keyboard("profile_back"),
            )
            if state:
                await state.finish()
            return
        else:
            await redis.set(user_usage_key, "0", ex=RECORD_INTERVAL)

    if user_usage == "1":
        await call.message.edit_text(
            "⚠️ Ты уже использовал этот промокод.",
            reply_markup=create_close_back_keyboard("profile_back"),
        )
        if state:
            await state.finish()
        return

    if call.data == "confirm_promo_code_yes":
        if promo_code.promo_type == "subscription":
            subscription_duration_seconds = int(promo_code.value)
            subscription_duration = timedelta(seconds=subscription_duration_seconds)

            if user.subscription_end:
                user.subscription_end += subscription_duration
            else:
                user.subscription_end = datetime.now() + subscription_duration

        new_usage = PromoCodeUsage(user_id=user.id, promo_code_id=promo_code.id)
        session.add(new_usage)
        session.commit()

        usage_count_key = f"promo_code:{promo_code.id}:usage_count"
        await redis.incr(usage_count_key)
        await redis.set(user_usage_key, "1", ex=RECORD_INTERVAL)

        subscription_end_key = f"user:{user_id}:subscription_end"
        await redis.delete(subscription_end_key)
        logger.debug(f"Кэш subscription_end для пользователя {user_id} удален.")

        await call.message.edit_text(
            f"✅ Промокод '{promo_code.code}' успешно применен!",
            reply_markup=create_close_back_keyboard("profile_back"),
        )
    elif call.data == "confirm_promo_code_no":
        await call.message.edit_text(
            "❌ Применение промокода отменено.",
            reply_markup=create_close_back_keyboard("profile_back"),
        )

    if state:
        await state.finish()
