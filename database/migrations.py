from utils.logger import logger

def run_migrations(conn):
    """Выполнение миграций базы данных"""
    try:
        # Добавляем колонку updated_at если её нет
        try:
            conn.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            logger.info("Колонка updated_at добавлена в таблицу users")
        except Exception as e:
            if "duplicate column name" not in str(e):
                logger.warning(f"Ошибка при добавлении колонки updated_at: {e}")

        # Добавляем колонку role если её нет
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            logger.info("Колонка role добавлена в таблицу users")
        except Exception as e:
            if "duplicate column name" not in str(e):
                logger.warning(f"Ошибка при добавлении колонки role: {e}")

    except Exception as e:
        logger.error(f"Ошибка выполнения миграций: {e}")