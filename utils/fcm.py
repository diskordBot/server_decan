# utils/fcm.py
import os
import json
import requests
import google.auth.transport.requests
import google.oauth2.service_account
from config import SERVER_CONFIG

SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
PROJECT_ID = "decanprogeck"  # ваш project_id (из service account JSON)

def _get_sa_path() -> str:
    # Путь берём из FCM_SERVICE_ACCOUNT или GOOGLE_APPLICATION_CREDENTIALS
    p = SERVER_CONFIG.get("fcm_service_account") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not p or not os.path.exists(p):
        raise FileNotFoundError(f"Service account JSON not found: '{p or 'EMPTY'}'")
    return p

def get_access_token() -> str:
    creds_path = _get_sa_path()
    creds = google.oauth2.service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    return creds.token

def send_news_to_topic(title: str, body: str, data: dict | None = None, topic: str = "news") -> None:
    """
    Отправка пуша через FCM HTTP v1. Payload ДОЛЖЕН быть вида {"message": {...}}.
    """
    access_token = get_access_token()
    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

    # HTTP v1 ожидает корень "message", а не legacy "to"/"priority" на верхнем уровне
    message = {
        "topic": topic,
        "notification": {
            "title": title or "Новости",
            "body": (body or "")[:180],
        },
        "data": data or {},
        # Рекомендуется задать платформенные секции (канал, звук, приоритет):
        "android": {
            "priority": "HIGH",
            "notification": {
                "channel_id": "news_channel",
                "sound": "default",
            },
        },
        "apns": {
            "headers": {"apns-priority": "10"},
            "payload": {"aps": {"sound": "default"}},
        },
    }

    payload = {"message": message}
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {access_token}",
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
    if resp.status_code != 200:
        # логируем для дебага, но не валим сервер
        from utils.logger import logger
        logger.error(f"FCM v1 error {resp.status_code}: {resp.text}")
