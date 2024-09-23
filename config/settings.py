import os
from dotenv import load_dotenv
import logging

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "bot")

# Попытка получить данные для PostgreSQL из переменных окружения
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", None)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", BOT_NAME)

# Используем PostgreSQL как основное подключение, если переменные заданы
if POSTGRES_USER and POSTGRES_DB:
    if POSTGRES_PASSWORD:
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    else:
        DATABASE_URL = f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    # Если данные для PostgreSQL не заданы, используем SQLite как резервный вариант
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, f'database/{BOT_NAME}.db')}"

# Настройки Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

REDIS_SETTINGS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": REDIS_DB,
}

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL, logging.INFO)
