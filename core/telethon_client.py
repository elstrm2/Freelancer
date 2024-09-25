from telethon import TelegramClient
from config.settings import API_HASH, API_ID

telethon_client = TelegramClient(None, API_ID, API_HASH)
