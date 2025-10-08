from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.teacher_schedule import router as teacher_schedule_router
from config import SERVER_CONFIG
from utils.logger import setup_logging, logger
from database.connection import init_database
from api import users, schedule, groups, health, news, settings, students, teachers
from api.announcements import router as announcements_router  # 👈 ПРАВИЛЬНО

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_database()
        logger.info("Сервер успешно запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {e}")
        raise
    yield
    try:
        logger.info("Сервер завершает работу")
    except Exception as e:
        logger.error(f"Ошибка при завершении работы: {e}")

app = FastAPI(
    title="Decanat Project API",
    description="API для мобильного приложения кафедры ПМИИ",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
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
app.include_router(news.router, prefix="/api", tags=["News"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(students.router, prefix="/api", tags=["Students"])
app.include_router(teachers.router, prefix="/api", tags=["Teachers"])
app.include_router(teacher_schedule_router, prefix="/api")
app.include_router(announcements_router, prefix="/api", tags=["Announcements"])  # ✅ теперь корректно

@app.get("/")
async def root():
    return {
        "message": "Decanat Project API Server",
        "version": "1.2.3",
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
