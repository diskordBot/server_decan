import logging
import sys

def setup_logging():
    """Настройка логирования с поддержкой UTF-8"""
    # Удаляем старые хендлеры (если логгер настраивается повторно)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Хендлер для файла с явной кодировкой UTF-8
    file_handler = logging.FileHandler('server.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Базовая настройка
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )

# Экспорт логгера
logger = logging.getLogger(__name__)
