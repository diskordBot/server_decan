# database/migrations.py
from utils.logger import logger
import sqlite3

def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row["name"] == column for row in cur.fetchall())

def run_migrations(conn: sqlite3.Connection):
    """Безопасные миграции: добавляем колонки, если их нет, и заполняем NULL'ы."""
    try:
        # users.role
        if not _has_column(conn, "users", "role"):
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT")
            logger.info("Миграция: добавлена колонка users.role")
            conn.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

        # users.updated_at
        if not _has_column(conn, "users", "updated_at"):
            conn.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")
            logger.info("Миграция: добавлена колонка users.updated_at")
        conn.execute("UPDATE users SET updated_at = COALESCE(updated_at, datetime('now'))")

        # user_settings.updated_at
        if not _has_column(conn, "user_settings", "updated_at"):
            conn.execute("ALTER TABLE user_settings ADD COLUMN updated_at DATETIME")
            logger.info("Миграция: добавлена колонка user_settings.updated_at")
        conn.execute("UPDATE user_settings SET updated_at = COALESCE(updated_at, datetime('now'))")

        conn.commit()

    except Exception as e:
        logger.error(f"Ошибка выполнения миграций: {e}")
        # не пробрасываем — лучше иметь рабочую БД с неполной миграцией, чем падать на старте
