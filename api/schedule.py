# api/schedule.py
from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection
from utils.logger import logger
from models.schedule_models import ScheduleData

router = APIRouter()

@router.post("/schedule")
def save_schedule(schedule_data: ScheduleData):
    """Сохранение расписания (обе недели разом)"""
    try:
        with get_db_connection() as conn:
            # убедимся, что группа есть
            cur = conn.execute("SELECT 1 FROM schedule_groups WHERE group_name = ?", (schedule_data.group,))
            if not cur.fetchone():
                conn.execute("INSERT INTO schedule_groups (group_name) VALUES (?)", (schedule_data.group,))
                logger.info(f"Добавлена новая группа: {schedule_data.group}")

            # полностью пересобираем расписание для группы
            conn.execute("DELETE FROM schedule WHERE group_name = ?", (schedule_data.group,))

            # верхняя неделя
            for day, lessons in schedule_data.upper_week.items():
                for lesson in lessons:
                    conn.execute(
                        """INSERT INTO schedule
                           (group_name, week_type, day_name, lesson_number, subject, teacher, classroom, lesson_type)
                           VALUES (?, 'upper', ?, ?, ?, ?, ?, ?)""",
                        (schedule_data.group, day, lesson["lesson_number"], lesson["subject"], lesson["teacher"], lesson["classroom"], lesson["type"])
                    )

            # нижняя неделя
            for day, lessons in schedule_data.lower_week.items():
                for lesson in lessons:
                    conn.execute(
                        """INSERT INTO schedule
                           (group_name, week_type, day_name, lesson_number, subject, teacher, classroom, lesson_type)
                           VALUES (?, 'lower', ?, ?, ?, ?, ?, ?)""",
                        (schedule_data.group, day, lesson["lesson_number"], lesson["subject"], lesson["teacher"], lesson["classroom"], lesson["type"])
                    )

            conn.commit()
            logger.info(f"Расписание сохранено для группы: {schedule_data.group}")
            return {"message": "Расписание сохранено успешно"}

    except Exception as e:
        logger.error(f"Ошибка сохранения расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения расписания")

@router.get("/schedule/{group_name}/{week_type}")
def get_schedule(group_name: str, week_type: str):
    """Расписание для одной недели (экран студента)"""
    try:
        if week_type not in ("upper", "lower"):
            raise HTTPException(status_code=400, detail="Неверный тип недели")

        with get_db_connection() as conn:
            cur = conn.execute(
                """
                SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type
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
                  lesson_number
                """,
                (group_name, week_type)
            )

            data = {}
            for row in cur.fetchall():
                day = row["day_name"]
                data.setdefault(day, []).append({
                    "lesson_number": row["lesson_number"],
                    "subject": row["subject"],
                    "teacher": row["teacher"],
                    "classroom": row["classroom"],
                    "type": row["lesson_type"],   # клиент ждёт ключ 'type'
                })
            return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения расписания")

@router.get("/schedule/{group_name}")
def get_full_schedule(group_name: str):
    """
    Полная выдача для редактирования (обе недели).
    Возвращает:
    {
      "upper_week": { "Понедельник": [ ... ], ... },
      "lower_week": { "Понедельник": [ ... ], ... }
    }
    """
    try:
        with get_db_connection() as conn:
            def fetch_week(week: str):
                cur = conn.execute(
                    """
                    SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type
                    FROM schedule
                    WHERE group_name = ? AND week_type = ?
                    ORDER BY
                      CASE day_name
                        WHEN 'Понедельник' THEN 1
                        WHEN 'Вторник' THEN 2
                        WHEN 'Среда' THEN 3
                        WHEN 'Четверг' THEN 4
                        WHEN 'Пятница' THEN 5
                      END,
                      lesson_number
                    """,
                    (group_name, week)
                )
                out = {}
                for row in cur.fetchall():
                    day = row["day_name"]
                    out.setdefault(day, []).append({
                        "lesson_number": row["lesson_number"],
                        "subject": row["subject"],
                        "teacher": row["teacher"],
                        "classroom": row["classroom"],
                        "type": row["lesson_type"],
                    })
                return out

            return {
                "upper_week": fetch_week("upper"),
                "lower_week": fetch_week("lower"),
            }
    except Exception as e:
        logger.error(f"Ошибка получения полного расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения расписания")
