from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime
from database.models import User
from config.settings import DATABASE_URL

load_dotenv()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


def validate_boolean(value):
    return value in ["0", "1"]


def add_user():
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
    last_name = input("Введи фамилию пользователя (можно оставить пустым): ").strip()

    while True:
        is_admin = input(
            "Является ли пользователь администратором? (1 - Да, 0 - Нет): "
        ).strip()
        if validate_boolean(is_admin):
            is_admin = bool(int(is_admin))
            break
        print("Неверное значение. Введите 1 для Да или 0 для Нет.")

    existing_user = session.query(User).filter_by(user_id=user_id).first()
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
    session.commit()
    print("Пользователь успешно добавлен.")


add_user()
session.close()
