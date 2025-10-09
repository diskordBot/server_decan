# database/models.py
from utils.logger import logger
import sqlite3

def create_tables(conn: sqlite3.Connection):
    """Создание таблиц (актуальная схема). Повторные вызовы безопасны."""
    try:
        # USERS — добавлены last_seen
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                device_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME  -- NEW: время последней активности
            )
        """)

        # STUDENTS — таблица студентов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                login TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                group_name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (group_name) REFERENCES schedule_groups (group_name) ON DELETE CASCADE
            )
        """)

        # TEACHERS — новая таблица преподавателей (добавляем UNIQUE для full_name)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                full_name TEXT UNIQUE NOT NULL,  -- ДОБАВЛЕНО UNIQUE
                login TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                department TEXT,
                position TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)

        # TEACHER SCHEDULE - расписание преподавателей (исправлен внешний ключ)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS teacher_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_name TEXT NOT NULL,
                week_type TEXT NOT NULL,              -- 'upper' | 'lower'
                day_name TEXT NOT NULL,               -- 'Понедельник' ... 'Суббота'
                lesson_number INTEGER NOT NULL,
                subject TEXT NOT NULL,
                group_name TEXT NOT NULL,             -- группа студентов
                classroom TEXT NOT NULL,
                lesson_type TEXT NOT NULL,           -- тип занятия
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_name) REFERENCES teachers (full_name) ON DELETE CASCADE
            )
        """)

        # SETTINGS — глобальные параметры
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица новостей
        conn.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                image_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # USER SETTINGS
        conn.execute("""
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
        """)

        # GROUPS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedule_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # SCHEDULE
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL,
                week_type TEXT NOT NULL,              -- 'upper' | 'lower'
                day_name TEXT NOT NULL,               -- 'Понедельник' ... 'Суббота'
                lesson_number INTEGER NOT NULL,
                subject TEXT NOT NULL,
                teacher TEXT NOT NULL,
                classroom TEXT NOT NULL,
                lesson_type TEXT NOT NULL,           -- хранится как lesson_type
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_name) REFERENCES schedule_groups (group_name) ON DELETE CASCADE
            )
        """)

        # INDEXES
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedule_group_week 
            ON schedule (group_name, week_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedule_group_week_day 
            ON schedule (group_name, week_type, day_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_user_id 
            ON users (user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_settings_user_id 
            ON user_settings (user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_user_id 
            ON students (user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_login 
            ON students (login)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_group 
            ON students (group_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teachers_user_id 
            ON teachers (user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teachers_login 
            ON teachers (login)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teachers_department 
            ON teachers (department)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teachers_full_name 
            ON teachers (full_name)  -- ДОБАВЛЕН новый индекс
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teacher_schedule_name_week 
            ON teacher_schedule (teacher_name, week_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teacher_schedule_name_week_day 
            ON teacher_schedule (teacher_name, week_type, day_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teacher_schedule_teacher_name 
            ON teacher_schedule (teacher_name)
        """)

        logger.info("Схема БД создана/обновлена")

    except Exception as e:
        logger.error(f"Ошибка создания таблиц: {e}")
        raise