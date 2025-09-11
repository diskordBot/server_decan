from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Decanat Project API",
    description="API для мобильного приложения кафедры ПМИИ",
    version="1.0.0"
)

# Добавьте CORS middleware для работы с Flutter приложением
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки, в production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Модели данных
class UserCreate(BaseModel):
    device_info: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    created_at: str


class SettingsUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    vibration_enabled: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    language: Optional[str] = None
    font_size: Optional[str] = None


class GroupCreate(BaseModel):
    group_name: str


class ScheduleData(BaseModel):
    group: str
    upper_week: Dict[str, List[Dict[str, Any]]]
    lower_week: Dict[str, List[Dict[str, Any]]]


# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('decanat_app.db')
    conn.row_factory = sqlite3.Row
    return conn


# Инициализация базы данных при запуске
@app.on_event("startup")
def startup():
    conn = get_db_connection()
    try:
        # Таблица пользователей
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                device_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица групп расписания
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schedule_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
    finally:
        conn.close()


# Эндпоинты API
@app.post("/api/users", response_model=UserResponse)
def create_user(user_data: UserCreate):
    """Создание нового пользователя с уникальным ID"""
    conn = get_db_connection()
    try:
        # Генерация уникального ID (6 цифр как в вашем приложении)
        user_id = str(uuid.uuid4().int)[:6]

        # Вставляем пользователя
        conn.execute(
            "INSERT INTO users (user_id, device_info) VALUES (?, ?)",
            (user_id, user_data.device_info)
        )

        # Создаем настройки по умолчанию
        conn.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,)
        )

        conn.commit()

        logger.info(f"Создан новый пользователь: {user_id}")

        return {
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }

    except sqlite3.IntegrityError:
        # Если ID уже существует (маловероятно), пробуем снова
        return create_user(user_data)
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания пользователя")
    finally:
        conn.close()


@app.get("/api/users/{user_id}/settings")
def get_user_settings(user_id: str):
    """Получение настроек пользователя"""
    conn = get_db_connection()
    try:
        # Сначала проверяем существование пользователя
        cursor = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        )
        if not cursor.fetchone():
            # Если пользователь не существует, создаем его с настройками по умолчанию
            conn.execute(
                "INSERT INTO users (user_id) VALUES (?)",
                (user_id,)
            )
            conn.execute(
                "INSERT INTO user_settings (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            logger.info(f"Создан новый пользователь: {user_id}")

        # Получаем настройки
        cursor = conn.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        settings = cursor.fetchone()

        if not settings:
            # Если настроек нет, создаем их
            conn.execute(
                "INSERT INTO user_settings (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()

            # Повторно получаем настройки
            cursor = conn.execute(
                "SELECT * FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            settings = cursor.fetchone()

        return {
            "notifications_enabled": bool(settings['notifications_enabled']),
            "vibration_enabled": bool(settings['vibration_enabled']),
            "sound_enabled": bool(settings['sound_enabled']),
            "language": settings['language'],
            "font_size": settings['font_size']
        }

    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")
    finally:
        conn.close()


@app.put("/api/users/{user_id}/settings")
def update_user_settings(user_id: str, settings: SettingsUpdate):
    """Обновление настроек пользователя"""
    conn = get_db_connection()
    try:
        # Проверяем существование пользователя
        cursor = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        )
        if not cursor.fetchone():
            # Если пользователь не существует, создаем его
            conn.execute(
                "INSERT INTO users (user_id) VALUES (?)",
                (user_id,)
            )
            conn.execute(
                "INSERT INTO user_settings (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            logger.info(f"Создан новый пользователь: {user_id}")

        # Строим динамический запрос для обновления
        update_fields = []
        update_values = []

        if settings.notifications_enabled is not None:
            update_fields.append("notifications_enabled = ?")
            update_values.append(int(settings.notifications_enabled))

        if settings.vibration_enabled is not None:
            update_fields.append("vibration_enabled = ?")
            update_values.append(int(settings.vibration_enabled))

        if settings.sound_enabled is not None:
            update_fields.append("sound_enabled = ?")
            update_values.append(int(settings.sound_enabled))

        if settings.language is not None:
            update_fields.append("language = ?")
            update_values.append(settings.language)

        if settings.font_size is not None:
            update_fields.append("font_size = ?")
            update_values.append(settings.font_size)

        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(user_id)

            query = f"UPDATE user_settings SET {', '.join(update_fields)} WHERE user_id = ?"
            conn.execute(query, update_values)
            conn.commit()

        logger.info(f"Настройки пользователя {user_id} обновлены")
        return {"message": "Настройки успешно обновлены"}

    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настроек: {str(e)}")
    finally:
        conn.close()


@app.get("/api/groups")
def get_groups():
    """Получение списка всех групп"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT DISTINCT group_name FROM schedule_groups ORDER BY group_name")
        groups = [row['group_name'] for row in cursor.fetchall()]

        if not groups:
            # Возвращаем дефолтные группы если нет в базе
            return [
                'КИ-25', 'СП-25а', 'СП-25б', 'КСЦ-25', 'ПИ-25а', 'ПИ-25б', 'ПИ-25в',
                'ИИ-25а', 'ИИ-25б', 'ИНФ-25', 'САУ-25', 'ПМКИ-25', 'КИ-24', 'СП-24',
                'КСЦ-24', 'ПИ-24а', 'ПИ-24б', 'ИИ-24', 'ИНФ-24', 'САУ-24'
            ]

        return groups
    except Exception as e:
        logger.error(f"Ошибка получения групп: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения групп")
    finally:
        conn.close()


@app.post("/api/groups")
def create_group(group_data: GroupCreate):
    """Добавление новой группы"""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO schedule_groups (group_name) VALUES (?)",
            (group_data.group_name,)
        )
        conn.commit()
        return {"message": "Группа добавлена успешно"}
    except Exception as e:
        logger.error(f"Ошибка добавления группы: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления группы")
    finally:
        conn.close()


@app.post("/api/schedule")
def save_schedule(schedule_data: ScheduleData):
    """Сохранение расписания"""
    conn = get_db_connection()
    try:
        # Удаляем старое расписание группы
        conn.execute(
            "DELETE FROM schedule WHERE group_name = ?",
            (schedule_data.group,)
        )

        # Сохраняем верхнюю неделю
        for day, lessons in schedule_data.upper_week.items():
            for lesson in lessons:
                conn.execute(
                    """INSERT INTO schedule 
                    (group_name, week_type, day_name, lesson_number, subject, 
                     teacher, classroom, lesson_type) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (schedule_data.group, 'upper', day, lesson['lesson_number'],
                     lesson['subject'], lesson['teacher'], lesson['classroom'],
                     lesson['type'])
                )

        # Сохраняем нижнюю неделю
        for day, lessons in schedule_data.lower_week.items():
            for lesson in lessons:
                conn.execute(
                    """INSERT INTO schedule 
                    (group_name, week_type, day_name, lesson_number, subject, 
                     teacher, classroom, lesson_type) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (schedule_data.group, 'lower', day, lesson['lesson_number'],
                     lesson['subject'], lesson['teacher'], lesson['classroom'],
                     lesson['type'])
                )

        conn.commit()
        return {"message": "Расписание сохранено успешно"}
    except Exception as e:
        logger.error(f"Ошибка сохранения расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения расписания")
    finally:
        conn.close()


@app.get("/api/schedule/{group_name}/{week_type}")
def get_schedule(group_name: str, week_type: str):
    """Получение расписания для группы"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type 
               FROM schedule 
               WHERE group_name = ? AND week_type = ? 
               ORDER BY 
                 CASE day_name
                   WHEN 'Понедельник' THEN 1
                   WHEN 'Вторник' THEN 2
                   WHEN 'Среда' THEN 3
                   WHEN 'Четверг' THEN 4
                   WHEN 'Пятница' THEN 5
                   WHEN 'Суббота' THEN 6
                 END,
                 lesson_number""",
            (group_name, week_type)
        )

        schedule_data = {}
        for row in cursor.fetchall():
            day_name = row['day_name']
            if day_name not in schedule_data:
                schedule_data[day_name] = []

            schedule_data[day_name].append({
                'lesson_number': row['lesson_number'],
                'subject': row['subject'],
                'teacher': row['teacher'],
                'classroom': row['classroom'],
                'type': row['lesson_type']
            })

        return schedule_data
    except Exception as e:
        logger.error(f"Ошибка получения расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения расписания")
    finally:
        conn.close()


@app.get("/api/schedule/{group_name}")
def get_full_schedule(group_name: str):
    """Получение полного расписания для группы (обе недели)"""
    conn = get_db_connection()
    try:
        # Получаем верхнюю неделю
        cursor_upper = conn.execute(
            """SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type 
               FROM schedule 
               WHERE group_name = ? AND week_type = 'upper' 
               ORDER BY 
                 CASE day_name
                   WHEN 'Понедельник' THEN 1
                   WHEN 'Вторник' THEN 2
                   WHEN 'Среда' THEN 3
                   WHEN 'Четверг' THEN 4
                   WHEN 'Пятница' THEN 5
                   WHEN 'Суббота' THEN 6
                 END,
                 lesson_number""",
            (group_name,)
        )

        upper_week = {}
        for row in cursor_upper.fetchall():
            day_name = row['day_name']
            if day_name not in upper_week:
                upper_week[day_name] = []
            upper_week[day_name].append({
                'lesson_number': row['lesson_number'],
                'subject': row['subject'],
                'teacher': row['teacher'],
                'classroom': row['classroom'],
                'type': row['lesson_type']
            })

        # Получаем нижнюю неделю
        cursor_lower = conn.execute(
            """SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type 
               FROM schedule 
               WHERE group_name = ? AND week_type = 'lower' 
               ORDER BY 
                 CASE day_name
                   WHEN 'Понедельник' THEN 1
                   WHEN 'Вторник' THEN 2
                   WHEN 'Среда' THEN 3
                   WHEN 'Четверг' THEN 4
                   WHEN 'Пятница' THEN 5
                   WHEN 'Суббота' THEN 6
                 END,
                 lesson_number""",
            (group_name,)
        )

        lower_week = {}
        for row in cursor_lower.fetchall():
            day_name = row['day_name']
            if day_name not in lower_week:
                lower_week[day_name] = []
            lower_week[day_name].append({
                'lesson_number': row['lesson_number'],
                'subject': row['subject'],
                'teacher': row['teacher'],
                'classroom': row['classroom'],
                'type': row['lesson_type']
            })

        return {
            'group': group_name,
            'upper_week': upper_week,
            'lower_week': lower_week
        }

    except Exception as e:
        logger.error(f"Ошибка получения полного расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения расписания")
    finally:
        conn.close()


@app.get("/api/health")
def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/")
def root():
    return {"message": "Decanat Project API Server", "version": "1.2.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="185.72.144.22", port=22)
