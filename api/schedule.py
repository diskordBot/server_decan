from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection
from utils.logger import logger
from models.schedule_models import ScheduleData

router = APIRouter()


@router.post("/schedule")
def save_schedule(schedule_data: ScheduleData):
    """Сохранение расписания"""
    try:
        with get_db_connection() as conn:
            # Проверяем существование группы
            cursor = conn.execute(
                "SELECT 1 FROM schedule_groups WHERE group_name = ?",
                (schedule_data.group,)
            )
            if not cursor.fetchone():
                # Если группы нет, добавляем её
                conn.execute(
                    "INSERT INTO schedule_groups (group_name) VALUES (?)",
                    (schedule_data.group,)
                )
                logger.info(f"Добавлена новая группа: {schedule_data.group}")

            # Удаляем старое расписание группы
            conn.execute("DELETE FROM schedule WHERE group_name = ?", (schedule_data.group,))

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
            logger.info(f"Расписание сохранено для группы: {schedule_data.group}")
            return {"message": "Расписание сохранено успешно"}

    except Exception as e:
        logger.error(f"Ошибка сохранения расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения расписания")


@router.get("/schedule/{group_name}/{week_type}")
def get_schedule(group_name: str, week_type: str):
    """Получение расписания для группы"""
    try:
        with get_db_connection() as conn:
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


@router.get("/schedule/{group_name}")
def get_full_schedule(group_name: str):
    """Получение полного расписания для группы (обе недели)"""
    try:
        with get_db_connection() as conn:
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