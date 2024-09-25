import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from config.settings import (
    DATABASE_URL,
    LOG_LEVEL,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
)
from database.models import Base

load_dotenv()

SYNC_POSTGRES_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"


async def create_database_if_not_exists():
    try:
        engine = create_engine(
            SYNC_POSTGRES_URL,
            isolation_level="AUTOCOMMIT",
            echo=True if LOG_LEVEL is logging.DEBUG else False,
        )

        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'")
            )
            exists = result.scalar()

            if not exists:
                conn.execute(text(f"CREATE DATABASE {POSTGRES_DB}"))
                print(f"База данных {POSTGRES_DB} успешно создана.")
            else:
                print(f"База данных {POSTGRES_DB} уже существует.")
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        engine.dispose()


async def create_tables():
    try:
        engine = create_async_engine(
            DATABASE_URL,
            echo=True if LOG_LEVEL is logging.DEBUG else False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Таблицы успешно созданы.")
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
    finally:
        await engine.dispose()


async def main():
    await create_database_if_not_exists()
    await create_tables()


asyncio.run(main())
