from fastapi import APIRouter, HTTPException, Form, Depends, Query
from database.connection import get_db_connection
from utils.logger import logger
from datetime import datetime

router = APIRouter()

@router.post("/news")
async def add_news(
    title: str = Form(...),
    text: str = Form(...),
    image_url: str = Form(None)
):
    """Добавить новость (бот вызывает)"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO news (title, text, image_url, created_at) VALUES (?, ?, ?, ?)",
                (title, text, image_url, datetime.utcnow())
            )
            conn.commit()
        logger.info(f"Добавлена новость: {title}")
        return {"message": "Новость добавлена"}
    except Exception as e:
        logger.error(f"Ошибка добавления новости: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления новости")

@router.get("/news")
async def get_news():
    """Получить список новостей"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                "SELECT id, title, text, image_url, created_at FROM news ORDER BY created_at DESC"
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "text": row["text"],
                    "image_url": row["image_url"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Ошибка получения новостей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения новостей")


@router.delete("/news/{news_id}")
async def delete_news(news_id: int, user_id: str = Query(...)):
    """
    Удалить новость по ID (только admin или developer).
    user_id нужно передавать как параметр запроса (?user_id=XXXXXX).
    """
    try:
        with get_db_connection() as conn:
            # Проверяем роль пользователя
            cur = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            role = row["role"]
            if role not in ("admin", "developer"):
                raise HTTPException(status_code=403, detail="Доступ запрещен")

            # Проверяем наличие новости
            cur = conn.execute("SELECT id FROM news WHERE id = ?", (news_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Новость не найдена")

            # Удаляем новость
            conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
            conn.commit()

        logger.info(f"Пользователь {user_id} ({role}) удалил новость ID={news_id}")
        return {"message": "Новость удалена успешно"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления новости: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления новости")