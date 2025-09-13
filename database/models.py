from utils.logger import logger

def create_tables(conn):
    """Создание таблиц базы данных"""
    try:
        # Таблица пользователей - СНАЧАЛА создаем без колонки role
        conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    device_info TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        # Таблица настроек пользователей
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                notifications_enabled BOOLEAN DEFAULT 1,
                vibration_enabled BOOLEAN DEFAULT 1,
                sound_enabled BOOLEAN DEFAULT 1,
                language TEXT DEFAULT 'Русский',
                font_size TEXT DEFAULT 'Средний',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')

        # Таблица групп расписания
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schedule_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица расписания
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL,
                week_type TEXT NOT NULL,
                day_name TEXT NOT NULL,
                lesson_number INTEGER NOT NULL,
                subject TEXT NOT NULL,
                teacher TEXT NOT NULL,
                classroom TEXT NOT NULL,
                lesson_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_name) REFERENCES schedule_groups (group_name) ON DELETE CASCADE
            )
        ''')

        # Индексы для улучшения производительности
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_schedule_group_week 
            ON schedule (group_name, week_type)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_schedule_group_week_day 
            ON schedule (group_name, week_type, day_name)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_user_id 
            ON users (user_id)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_settings_user_id 
            ON user_settings (user_id)
        ''')

        # Создаем пользователя-разработчика с ID 000000
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, role) VALUES (?, ?)",
                ('000000', 'developer')
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)",
                ('000000',)
            )
            logger.info("Пользователь-разработчик 000000 создан")
        except Exception as e:
            logger.error(f"Ошибка создания пользователя-разработчика: {e}")

    except Exception as e:
        logger.error(f"Ошибка создания таблиц: {e}")
        raise