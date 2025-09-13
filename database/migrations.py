from utils.logger import logger

def run_migrations(conn):
    """Выполнение миграций базы данных"""
    try:
        # 1. Добавляем колонку role с дефолтным значением
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            logger.info("Колонка role добавлена в таблицу users")
        except Exception as e:
            if "duplicate column name" not in str(e):
                logger.warning(f"Ошибка при добавлении колонки role: {e}")

        # 2. Добавляем колонку updated_at с дефолтным значением
        try:
            conn.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            logger.info("Колонка updated_at добавлена в таблицу users")
        except Exception as e:
            if "duplicate column name" not in str(e):
                logger.warning(f"Ошибка при добавлении колонки updated_at: {e}")

        # 3. Обновляем существующие записи
        try:
            conn.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
            conn.execute("UPDATE users SET updated_at = datetime('now') WHERE updated_at IS NULL")
        except Exception as e:
            logger.warning(f"Ошибка обновления данных: {e}")

    except Exception as e:
        logger.error(f"Ошибка выполнения миграций: {e}")