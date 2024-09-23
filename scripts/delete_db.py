import psycopg2
from config.settings import DATABASE_URL
import os


def drop_database():
    db_name = DATABASE_URL.split("/")[-1]
    db_connection_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"

    try:
        conn = psycopg2.connect(db_connection_url)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()

        if exists:
            cur.execute(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db_name}'"
            )

            cur.execute(f"DROP DATABASE {db_name}")
            print(f"База данных {db_name} успешно удалена.")
        else:
            print(f"База данных {db_name} не существует.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при удалении базы данных: {e}")
        raise


drop_database()
