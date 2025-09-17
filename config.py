import os
from dotenv import load_dotenv

load_dotenv()
SERVER_CONFIG = {
    "host": os.getenv("SERVER_HOST", "185.72.144.22"),
    "port": int(os.getenv("SERVER_PORT", 8000)),
    "database_url": os.getenv("DATABASE_URL", "decanat_app.db"),
    "backup_enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",
}
