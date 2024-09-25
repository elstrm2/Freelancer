import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from config.settings import (
    LOG_LEVEL,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
)

load_dotenv()

SYNC_POSTGRES_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"


async def drop_database_if_exists():
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

            if exists:
                conn.execute(
                    text(
                        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{POSTGRES_DB}'"
                    )
                )

                conn.execute(text(f"DROP DATABASE {POSTGRES_DB}"))
                print(f"База данных {POSTGRES_DB} успешно удалена.")
            else:
                print(f"База данных {POSTGRES_DB} не существует.")
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
    except Exception as e:
        print(f"Ошибка при удалении базы данных: {e}")
    finally:
        engine.dispose()


async def main():
    await drop_database_if_exists()


asyncio.run(main())
