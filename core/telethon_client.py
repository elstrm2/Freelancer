import os
from telethon import TelegramClient
from config.settings import API_HASH, API_ID, PHONE_NUMBER, PASSWORD

session_file_path = os.path.join(os.path.dirname(__file__), "telethon_session")

telethon_client = TelegramClient(session_file_path, API_ID, API_HASH).start(
    phone=PHONE_NUMBER, password=PASSWORD
)
