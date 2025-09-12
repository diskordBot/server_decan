from fastapi import APIRouter
from datetime import datetime
from database.connection import get_db_connection
from utils.logger import logger

router = APIRouter()

@router.get("/health")
def health_check():
    """Проверка работоспособности сервера и базы данных"""
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        return {
            "status": "ok",
            "database": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья сервера: {e}")
        return {
            "status": "error",
            "database": "unavailable",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }