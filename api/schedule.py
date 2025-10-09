# api/schedule.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from database.connection import get_db_connection
from utils.logger import logger
from models.schedule_models import ScheduleData, LessonItem

router = APIRouter()

ALLOWED_DAYS = (
    "Понедельник", "Вторник", "Среда", "Четверг", "Пятница"
)


def _normalize_lessons(lessons: List[LessonItem]) -> List[Dict]:
    """
    Удаляем пустые предметы (без subject), приводим поля к нужным ключам,
    сортируем по lesson_number и ПЕРЕ-нумеровываем 1..N без «дыр».
    """
    out: List[Dict] = []
    for l in lessons:
        if not (l.subject or "").strip():
            # Не сохраняем «пустые» пары — это упрощает жизнь редактору
            continue
        out.append({
            "lesson_number": int(l.lesson_number),
            "subject": (l.subject or "").strip(),
            "teacher": (l.teacher or "").strip(),
            "classroom": (l.classroom or "").strip(),
            "type": (l.type or "").strip(),
        })

    # Сортировка по номеру пары
    out.sort(key=lambda x: x["lesson_number"])
    # Пере-нумерация 1..N
    for i, it in enumerate(out, start=1):
        it["lesson_number"] = i
    return out


@router.post("/schedule")
def save_schedule(schedule_data: ScheduleData):
    """
    Сохранение расписания (обе недели разом) для группы.
    Полностью пересобираем (DELETE + INSERT), чтобы избежать «зависших» строк.
    """
    try:
        with get_db_connection() as conn:
            # гарантируем существование группы
            cur = conn.execute(
                "SELECT 1 FROM schedule_groups WHERE group_name = ?",
                (schedule_data.group,)
            )
            if not cur.fetchone():
                conn.execute(
                    "INSERT INTO schedule_groups (group_name) VALUES (?)",
                    (schedule_data.group,)
                )
                logger.info(f"Добавлена новая группа: {schedule_data.group}")

            # полностью пересобираем расписание для группы
            conn.execute(
                "DELETE FROM schedule WHERE group_name = ?",
                (schedule_data.group,)
            )

            # Вставка по неделям
            for week_type, week_map in (
                ("upper", schedule_data.upper_week),
                ("lower", schedule_data.lower_week),
            ):
                for day, lessons in week_map.items():
                    if day not in ALLOWED_DAYS:
                        # Игнорируем «левые» дни, если такие пришли
                        continue

                    norm = _normalize_lessons(lessons)
                    for l in norm:
                        conn.execute(
                            """
                            INSERT INTO schedule
                               (group_name, week_type, day_name, lesson_number,
                                subject, teacher, classroom, lesson_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                schedule_data.group, week_type, day,
                                l["lesson_number"], l["subject"], l["teacher"],
                                l["classroom"], l["type"]
                            )
                        )
                    logger.info(
                        f"Сохранено: group={schedule_data.group} week={week_type} day={day}: {len(norm)} пар"
                    )

            conn.commit()
            logger.info(f"Расписание сохранено для группы: {schedule_data.group}")
            return {"message": "Расписание сохранено успешно"}

    except Exception as e:
        logger.error(f"Ошибка сохранения расписания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения расписания")


@router.get("/schedule/{group_name}/{week_type}")
def get_schedule(group_name: str, week_type: str):
    """
    Выдача расписания одной недели для группы — для мобильного «быстрого просмотра».
    Формат ответа: { "Понедельник": [{...}, ...], ... }
    """
    try:
        if week_type not in ("upper", "lower"):
            raise HTTPException(status_code=400, detail="Неверный тип недели")

        with get_db_connection() as conn:
            cur = conn.execute(
                f"""
                SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type
                FROM schedule
                WHERE group_name = ? AND week_type = ?
                  AND day_name IN ({",".join("?"*len(ALLOWED_DAYS))})
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
                (group_name, week_type, *ALLOWED_DAYS)
            )

            data: Dict[str, List[Dict]] = {}
            for row in cur.fetchall():
                day = row["day_name"]
                data.setdefault(day, []).append({
                    "lesson_number": row["lesson_number"],
                    "subject": row["subject"],
                    "teacher": row["teacher"],
                    "classroom": row["classroom"],
                    "type": row["lesson_type"],   # фронт ждёт ключ 'type'
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
    Полная выдача для редактора (обе недели).
    {
      "upper_week": { "Понедельник": [ ... ], ... },
      "lower_week": { "Понедельник": [ ... ], ... }
    }
    """
    try:
        with get_db_connection() as conn:

            def fetch_week(week: str) -> Dict[str, List[Dict]]:
                cur = conn.execute(
                    f"""
                    SELECT day_name, lesson_number, subject, teacher, classroom, lesson_type
                    FROM schedule
                    WHERE group_name = ? AND week_type = ?
                      AND day_name IN ({",".join("?"*len(ALLOWED_DAYS))})
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
                    (group_name, week, *ALLOWED_DAYS)
                )
                out: Dict[str, List[Dict]] = {}
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
