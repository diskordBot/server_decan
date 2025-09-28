# utils/fcm.py
import json
import google.auth.transport.requests
import google.oauth2.service_account
import requests
from config import SERVER_CONFIG

SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
PROJECT_ID = "decanprogeck"  # из service account JSON

def get_access_token():
    creds = google.oauth2.service_account.Credentials.from_service_account_file(
        SERVER_CONFIG["fcm_service_account"],
        scopes=SCOPES
    )
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    return creds.token

def send_news_to_topic(title: str, body: str, data: dict | None = None, topic: str = "news"):
    access_token = get_access_token()

    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

    payload = {
        "to": "/topics/news",
        "notification": {
            "title": title or "Новости",
            "body": (body or "")[:180],
            "sound": "default",
        },
        "data": {
            "type": "news",
            "image": "https://.../some-image.jpg",  # <-- добавь при наличии
        },
        "priority": "high",
    }

    headers = {
        "Content-Type": "application/json; UTF-8",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print("❌ Ошибка отправки:", response.status_code, response.text)
    else:
        print("✅ Пуш отправлен!")
