# api/settings.py
from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection
from utils.logger import logger

router = APIRouter()

@router.get("/settings/{key}")
def get_setting(key: str):
    """Получить глобальный параметр по ключу"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Параметр не найден")
            return {"key": key, "value": row["value"]}
    except Exception as e:
        logger.error(f"Ошибка получения параметра {key}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения параметра")

@router.put("/settings/{key}")
def update_setting(key: str, value: str):
    """Обновить/создать глобальный параметр"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (key, value))
            conn.commit()
        logger.info(f"Параметр {key} обновлен на {value}")
        return {"message": f"Параметр {key} обновлен", "value": value}
    except Exception as e:
        logger.error(f"Ошибка обновления параметра {key}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления параметра")
