# config.py
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_CONFIG = {
    "host": os.getenv("SERVER_HOST", "192.168.0.105"),
    "port": int(os.getenv("SERVER_PORT", 8000)),
    "database_url": os.getenv("DATABASE_URL", "decanat_app.db"),
    "backup_enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",

    # ключ FCM больше не нужен
    "fcm_service_account": os.getenv("FCM_SERVICE_ACCOUNT", "firebase_key.json"),
}

