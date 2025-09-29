# config.py
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_CONFIG = {
    "host": os.getenv("SERVER_HOST", "192.168.0.105"),
    "port": int(os.getenv("SERVER_PORT", 8000)),
    "database_url": os.getenv("DATABASE_URL", "decanat_app.db"),
    "backup_enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",

    # ❗️НЕ даём дефолта. Только из переменной окружения!
    #"fcm_service_account": os.getenv("FCM_SERVICE_ACCOUNT", "").strip(),
    "fcm_service_account": os.getenv("FCM_SERVICE_ACCOUNT", "/root/server_decan/keys/service-account.json"),

}
