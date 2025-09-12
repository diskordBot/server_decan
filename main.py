from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import SERVER_CONFIG
from utils.logger import setup_logging, logger
from database.connection import init_database
from utils.backup import backup_database  # Импорт из правильного места
from api import users, schedule, groups, health

# Настройка логирования
setup_logging()

app = FastAPI(
    title="Decanat Project API",
    description="API для мобильного приложения кафедры ПМИИ",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(schedule.router, prefix="/api", tags=["Schedule"])
app.include_router(groups.router, prefix="/api", tags=["Groups"])
app.include_router(health.router, prefix="/api", tags=["Health"])

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера"""
    try:
        init_database()
        logger.info("Сервер успешно запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Действия при завершении работы сервера"""
    try:
        backup_database()
        logger.info("Сервер завершает работу")
    except Exception as e:
        logger.error(f"Ошибка при завершении работы: {e}")

@app.get("/")
async def root():
    return {
        "message": "Decanat Project API Server",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
        log_level="info"
    )