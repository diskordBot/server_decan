from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection
from utils.logger import logger
from models.schedule_models import GroupCreate

router = APIRouter()

@router.get("/groups")
def get_groups():
    """Получение списка всех групп"""
    try:
        with get_db_connection() as conn:
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

@router.post("/groups")
def create_group(group_data: GroupCreate):
    """Добавление новой группы"""
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO schedule_groups (group_name) VALUES (?)", (group_data.group_name,))
            conn.commit()
            return {"message": "Группа добавлена успешно"}
    except Exception as e:
        logger.error(f"Ошибка добавления группы: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления группы")