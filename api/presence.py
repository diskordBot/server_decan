from fastapi import APIRouter, HTTPException
from database.connection import get_db_connection

router = APIRouter()

@router.post("/presence/ping")
def presence_ping(payload: dict):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    with get_db_connection() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        conn.execute("UPDATE users SET last_seen = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        conn.commit()
    return {"status": "ok"}
