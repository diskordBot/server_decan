import sqlite3
import os
from contextlib import contextmanager
from config import SERVER_CONFIG
from utils.logger import logger


@contextmanager
def get_db_connection():
    """Контекстный менеджер для безопасной работы с базой данных"""
    conn = None
    try:
        conn = sqlite3.connect(SERVER_CONFIG["database_url"], timeout=30)
        conn.row_factory = sqlite3.Row
        # Включаем поддержку внешних ключей и улучшаем надежность
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise
    finally:
        if conn:
            conn.close()


def check_database_integrity():
    """Проверка целостности базы данных"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            return result and result[0] == "ok"
    except Exception as e:
        logger.error(f"Ошибка проверки целостности БД: {e}")
        return False


def init_database():
    """Инициализация базы данных"""
    from .migrations import run_migrations
    from database.models import create_tables

    # Проверяем целостность базы данных
    if os.path.exists(SERVER_CONFIG["database_url"]) and not check_database_integrity():
        logger.warning("База данных повреждена, создаем новую")
        try:
            os.remove(SERVER_CONFIG["database_url"])
        except Exception as e:
            logger.error(f"Ошибка удаления поврежденной БД: {e}")

    try:
        with get_db_connection() as conn:
            create_tables(conn)
            run_migrations(conn)
            conn.commit()
            logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise