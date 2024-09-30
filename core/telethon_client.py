import getpass
import os
from telethon import TelegramClient
from config.settings import API_HASH, API_ID, PHONE_NUMBER, PASSWORD

# Получаем путь к папке 'core' (рядом с файлом telethon_client.py)
session_file_path = os.path.join(os.path.dirname(__file__), "telethon_session")

telethon_client = TelegramClient(session_file_path, API_ID, API_HASH).start(
    phone=PHONE_NUMBER,
    password=(
        PASSWORD if PASSWORD else lambda: getpass.getpass("Введи пароль от 2FA: ")
    ),
)
