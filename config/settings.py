import os
from dotenv import load_dotenv
import logging

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))

REDIS_SETTINGS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": REDIS_DB,
}

LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_LEVEL = getattr(logging, LOG_LEVEL)

RECORD_INTERVAL = int(os.getenv("RECORD_INTERVAL"))

POOL_SIZE = int(os.getenv("POOL_SIZE"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW"))

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

PHONE_NUMBER = os.getenv("PHONE_NUMBER")
PASSWORD = os.getenv("PASSWORD")
