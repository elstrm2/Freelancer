import getpass
from telethon import TelegramClient
from config.settings import API_HASH, API_ID, PHONE_NUMBER, PASSWORD

telethon_client = TelegramClient(None, API_ID, API_HASH).start(
    phone=PHONE_NUMBER,
    password=(
        PASSWORD if PASSWORD else lambda: getpass.getpass("Введи пароль от 2FA: ")
    ),
)
