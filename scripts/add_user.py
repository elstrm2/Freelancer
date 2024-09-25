import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv
from datetime import datetime
from database.models import User
from config.settings import DATABASE_URL, LOG_LEVEL

load_dotenv()

engine = create_async_engine(
    DATABASE_URL,
    echo=True if LOG_LEVEL is logging.DEBUG else False,
)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


def validate_boolean(value):
    return value in ["0", "1"]


async def add_user():
    async with AsyncSessionLocal() as session:
        while True:
            user_id = input("Введи ID пользователя: ").strip()
            if user_id.isdigit():
                user_id = int(user_id)
                break
            print("ID пользователя должно быть числом. Повтори попытку.")

        username = input(
            "Введи имя пользователя в Telegram (можно оставить пустым): "
        ).strip()
        first_name = input("Введи имя пользователя (можно оставить пустым): ").strip()
        last_name = input(
            "Введи фамилию пользователя (можно оставить пустым): "
        ).strip()

        while True:
            is_admin = input(
                "Является ли пользователь администратором? (1 - Да, 0 - Нет): "
            ).strip()
            if validate_boolean(is_admin):
                is_admin = bool(int(is_admin))
                break
            print("Неверное значение. Введи 1 для Да или 0 для Нет.")

        query = select(User).filter_by(user_id=user_id)
        session: AsyncSession
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Пользователь с таким user_id уже существует.")
            return

        new_user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
        )

        session.add(new_user)
        await session.commit()
        print("Пользователь успешно добавлен.")


asyncio.run(add_user())
