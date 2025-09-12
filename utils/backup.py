import os
import shutil
from datetime import datetime
from config import SERVER_CONFIG
from utils.logger import logger


def backup_database():
    """Создание резервной копии базы данных"""
    if not SERVER_CONFIG["backup_enabled"]:
        return

    try:
        if os.path.exists(SERVER_CONFIG["database_url"]):
            backup_name = f'decanat_app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(SERVER_CONFIG["database_url"], backup_name)
            logger.info(f"Создана резервная копия базы данных: {backup_name}")
    except Exception as e:
        logger.error(f"Ошибка создания резервной копии: {e}")