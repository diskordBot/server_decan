# teacher_schedule.py
from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection
from utils.logger import logger
from models.schedule_models import TeacherScheduleData, TeacherScheduleResponse

router = APIRouter()


@router.post("/teacher-schedule")
def save_teacher_schedule(schedule_data: TeacherScheduleData):
    """Сохранение расписания преподавателя (обе недели разом)"""
    try:
        with get_db_connection() as conn:
            # Проверяем, существует ли преподаватель в базе
            cur = conn.execute("SELECT 1 FROM teachers WHERE full_name = ?", (schedule_data.teacher_name,))
            if not cur.fetchone():
                raise HTTPException(status_code=404,
                                    detail=f"Преподаватель {schedule_data.teacher_name} не найден в базе. Сначала зарегистрируйте преподавателя.")

            # Начинаем транзакцию
            conn.execute("BEGIN TRANSACTION")

            try:
                # Полностью пересобираем расписание для преподавателя
                conn.execute("DELETE FROM teacher_schedule WHERE teacher_name = ?", (schedule_data.teacher_name,))

                # Верхняя неделя
                for day, lessons in schedule_data.upper_week.items():
                    for lesson in lessons:
                        conn.execute(
                            """INSERT INTO teacher_schedule
                               (teacher_name, week_type, day_name, lesson_number, subject, group_name, classroom, lesson_type)
                               VALUES (?, 'upper', ?, ?, ?, ?, ?, ?)""",
                            (schedule_data.teacher_name, day, lesson["lesson_number"],
                             lesson["subject"], lesson.get("group_name", ""),
                             lesson["classroom"], lesson["type"])
                        )

                # Нижняя неделя
                for day, lessons in schedule_data.lower_week.items():
                    for lesson in lessons:
                        conn.execute(
                            """INSERT INTO teacher_schedule
                               (teacher_name, week_type, day_name, lesson_number, subject, group_name, classroom, lesson_type)
                               VALUES (?, 'lower', ?, ?, ?, ?, ?, ?)""",
                            (schedule_data.teacher_name, day, lesson["lesson_number"],
                             lesson["subject"], lesson.get("group_name", ""),
                             lesson["classroom"], lesson["type"])
                        )

                conn.execute("COMMIT")
                logger.info(f"Расписание сохранено для преподавателя: {schedule_data.teacher_name}")
                return {"message": "Расписание преподавателя сохранено успешно"}

            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"Ошибка в транзакции сохранения расписания: {e}")
                raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сохранения расписания преподавателя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения расписания преподавателя")


# Остальные функции остаются без изменений...
@router.get("/teacher-schedule/{teacher_name}/{week_type}")
def get_teacher_schedule(teacher_name: str, week_type: str):
    """Расписание преподавателя для одной недели"""
    try:
        if week_type not in ("upper", "lower"):
            raise HTTPException(status_code=400, detail="Неверный тип недели")

        with get_db_connection() as conn:
            cur = conn.execute(
                """
                SELECT day_name, lesson_number, subject, group_name, classroom, lesson_type
                FROM teacher_schedule
                WHERE teacher_name = ? AND week_type = ?
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
                (teacher_name, week_type)
            )

            data = {}
            for row in cur.fetchall():
                day = row["day_name"]
                data.setdefault(day, []).append({
                    "lesson_number": row["lesson_number"],
                    "subject": row["subject"],
                    "group_name": row["group_name"],
                    "classroom": row["classroom"],
                    "type": row["lesson_type"],
                })
            return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения расписания преподавателя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения расписания преподавателя")


@router.get("/teacher-schedule/{teacher_name}")
def get_full_teacher_schedule(teacher_name: str):
    """Полное расписание преподавателя (обе недели)"""
    try:
        with get_db_connection() as conn:
            def fetch_week(week: str):
                cur = conn.execute(
                    """
                    SELECT day_name, lesson_number, subject, group_name, classroom, lesson_type
                    FROM teacher_schedule
                    WHERE teacher_name = ? AND week_type = ?
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
                    (teacher_name, week)
                )
                out = {}
                for row in cur.fetchall():
                    day = row["day_name"]
                    out.setdefault(day, []).append({
                        "lesson_number": row["lesson_number"],
                        "subject": row["subject"],
                        "group_name": row["group_name"],
                        "classroom": row["classroom"],
                        "type": row["lesson_type"],
                    })
                return out

            return {
                "upper_week": fetch_week("upper"),
                "lower_week": fetch_week("lower"),
            }
    except Exception as e:
        logger.error(f"Ошибка получения полного расписания преподавателя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения расписания преподавателя")


@router.get("/teachers")
def get_all_teachers():
    """Получение списка всех преподавателей"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                "SELECT full_name, department, position FROM teachers ORDER BY full_name"
            )

            teachers = []
            for row in cur.fetchall():
                teachers.append({
                    "full_name": row["full_name"],
                    "department": row["department"],
                    "position": row["position"]
                })

            return teachers
    except Exception as e:
        logger.error(f"Ошибка получения списка преподавателей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка преподавателей")