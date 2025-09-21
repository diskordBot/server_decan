# database/migrations.py
from utils.logger import logger
import sqlite3


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row["name"] == column for row in cur.fetchall())


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


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

        # МИГРАЦИЯ: Исправление таблицы teachers - добавление UNIQUE для full_name
        if _table_exists(conn, "teachers"):
            # Создаем временную таблицу с правильной структурой
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teachers_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    full_name TEXT UNIQUE NOT NULL,
                    login TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    department TEXT,
                    position TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            """)

            # Копируем данные из старой таблицы
            conn.execute("""
                INSERT INTO teachers_new 
                (id, user_id, full_name, login, password, department, position, created_at, updated_at)
                SELECT id, user_id, full_name, login, password, department, position, created_at, updated_at
                FROM teachers
            """)

            # Удаляем старую таблицу и переименовываем новую
            conn.execute("DROP TABLE teachers")
            conn.execute("ALTER TABLE teachers_new RENAME TO teachers")
            logger.info("Миграция: исправлена таблица teachers - добавлен UNIQUE для full_name")

        conn.commit()

    except Exception as e:
        logger.error(f"Ошибка выполнения миграций: {e}")
        # не пробрасываем — лучше иметь рабочую БД с неполной миграцией, чем падать на старте