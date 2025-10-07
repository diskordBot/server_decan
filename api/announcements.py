# api/announcements.py
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime, timezone
import os, json, threading

router = APIRouter()

# === Конфиг через ENV ===
NOTICE_PATH = os.getenv("UPDATE_NOTICE_JSON_PATH", "data/update_notice.json")
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "")  # если пусто — авторизация отключена

_lock = threading.RLock()
_notice_cache: Optional[dict] = None

class UpdateNotice(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    link: HttpUrl
    description: Optional[str] = Field(default=None, max_length=800)
    targetVersion: str = Field(min_length=1, max_length=32)
    createdAt: Optional[str] = None  # ISO-8601; если не задано — выставим на сервере

def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _load_from_file() -> Optional[dict]:
    if not os.path.exists(NOTICE_PATH):
        return None
    try:
        with open(NOTICE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _save_to_file(doc: Optional[dict]):
    _ensure_dir(NOTICE_PATH)
    if doc is None:
        # зачистка файла
        try:
            if os.path.exists(NOTICE_PATH):
                os.remove(NOTICE_PATH)
        except Exception:
            pass
        return
    with open(NOTICE_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

def _get_notice() -> Optional[dict]:
    global _notice_cache
    with _lock:
        if _notice_cache is not None:
            return _notice_cache
        _notice_cache = _load_from_file()
        return _notice_cache

def _set_notice(doc: Optional[dict]):
    global _notice_cache
    with _lock:
        _notice_cache = doc
        _save_to_file(doc)

def _require_admin(x_admin_key: Optional[str]):
    if not ADMIN_KEY:
        return  # авторизация отключена
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

@router.get("/announcements/latest")
def get_latest_notice():
    """
    Текущее глобальное уведомление (баннер) или 404 если отсутствует.
    """
    doc = _get_notice()
    if not doc:
        raise HTTPException(status_code=404, detail="No active notice")
    return doc

@router.put("/announcements/latest")
def put_latest_notice(
    payload: UpdateNotice,
    x_admin_key: Optional[str] = Header(None, convert_underscores=False),
):
    """
    Создать/обновить уведомление. Можно защитить через X-ADMIN-KEY (если ADMIN_API_KEY задан).
    """
    _require_admin(x_admin_key)

    doc = payload.model_dump(mode="json")
    if not doc.get("createdAt"):
        doc["createdAt"] = datetime.now(timezone.utc).isoformat()

    _set_notice(doc)
    return {"ok": True, "notice": doc}

@router.delete("/announcements/latest")
def delete_latest_notice(
    x_admin_key: Optional[str] = Header(None, convert_underscores=False),
):
    """
    Очистить уведомление.
    """
    _require_admin(x_admin_key)
    _set_notice(None)
    return {"ok": True}
