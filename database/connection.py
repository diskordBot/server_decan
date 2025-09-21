# database/connection.py
import sqlite3
import os
from contextlib import contextmanager
from config import SERVER_CONFIG
from utils.logger import logger
from data.groups import DEFAULT_GROUPS  # Импортируем из нового файла

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(SERVER_CONFIG["database_url"], timeout=30)
        conn.row_factory = sqlite3.Row
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
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            return result and result[0] == "ok"
    except Exception as e:
        logger.error(f"Ошибка проверки целостности БД: {e}")
        return False

def _ensure_system_developer(conn: sqlite3.Connection) -> None:
    """Создаём (или чиним) системного разработчика 000000"""
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, role, device_info) VALUES ('000000', 'developer', 'system')"
    )
    conn.execute(
        "UPDATE users SET role = 'developer' WHERE user_id = '000000' AND role <> 'developer'"
    )
    conn.execute(
        "INSERT OR IGNORE INTO user_settings (user_id) VALUES ('000000')"
    )
    logger.info("Пользователь-разработчик 000000 создан/обновлён")

def _ensure_news_table(conn: sqlite3.Connection) -> None:
    """Создание таблицы новостей, если её нет"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            image_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    logger.info("Таблица news проверена/создана")

def _ensure_default_groups(conn: sqlite3.Connection) -> None:
    """Создаем дефолтные группы при инициализации базы"""
    for group in DEFAULT_GROUPS:
        conn.execute(
            "INSERT OR IGNORE INTO schedule_groups (group_name) VALUES (?)",
            (group,)
        )
    logger.info("Дефолтные группы созданы/проверены")

def init_database():
    # относительный импорт внутри пакета database
    from .migrations import run_migrations
    from .models import create_tables

    # если файл есть, но битый — удалим
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
            _ensure_system_developer(conn)
            _ensure_news_table(conn)
            _ensure_default_groups(conn)
            conn.commit()
            logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise