# api/groups.py
from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection
from utils.logger import logger
from models.schedule_models import GroupCreate
from data.groups import DEFAULT_GROUPS  # список из data/groups.py

router = APIRouter()

def _ensure_default_groups(conn):
    """Добавляет дефолтные группы в базу, если их нет."""
    for group in DEFAULT_GROUPS:
        conn.execute(
            "INSERT OR IGNORE INTO schedule_groups (group_name) VALUES (?)",
            (group,)
        )
    conn.commit()

@router.get("/groups")
def get_groups():
    """Список групп из БД (с предварительной инициализацией дефолтов)."""
    try:
        with get_db_connection() as conn:
            _ensure_default_groups(conn)
            cur = conn.execute(
                "SELECT DISTINCT group_name FROM schedule_groups ORDER BY group_name"
            )
            groups = [row["group_name"] for row in cur.fetchall()]
            return groups
    except Exception as e:
        logger.error(f"Ошибка получения групп: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения групп")

@router.get("/groups/default")
def get_default_groups():
    """Дефолтный список групп без БД (из кода)."""
    return DEFAULT_GROUPS

@router.post("/groups")
def create_group(group_data: GroupCreate):
    """Добавить группу."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO schedule_groups (group_name) VALUES (?)",
                (group_data.group_name,)
            )
            conn.commit()
            return {"message": "Группа добавлена успешно"}
    except Exception as e:
        logger.error(f"Ошибка добавления группы: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления группы")

@router.get("/groups/debug")
def debug_groups():
    """Отладочная информация о группах."""
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT * FROM schedule_groups ORDER BY group_name")
            groups = [dict(row) for row in cur.fetchall()]
            return {
                "groups": groups,
                "count": len(groups),
                "default_groups": DEFAULT_GROUPS
            }
    except Exception as e:
        logger.error(f"Ошибка отладки групп: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отладки групп")
