import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from database.models import Base
from config.settings import DATABASE_URL

load_dotenv()


def create_database_if_not_exists():
    db_name = DATABASE_URL.split("/")[-1]
    db_connection_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"

    try:
        conn = psycopg2.connect(db_connection_url)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {db_name}")
            print(f"База данных {db_name} успешно создана.")
        else:
            print(f"База данных {db_name} уже существует.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при проверке или создании базы данных: {e}")
        raise


create_database_if_not_exists()

try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы.")
except OperationalError as e:
    print(f"Ошибка подключения к базе данных: {e}")
