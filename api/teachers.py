# api/teachers.py
from fastapi import APIRouter, HTTPException
import sqlite3
from database.connection import get_db_connection
from utils.logger import logger
from models.teacher_models import TeacherCreate, TeacherLogin, TeacherResponse
import bcrypt

router = APIRouter()

def hash_password(password: str) -> str:
    """Хэширование пароля"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@router.post("/teachers/register", response_model=TeacherResponse)
def register_teacher(teacher_data: TeacherCreate):
    """Регистрация нового преподавателя"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (teacher_data.user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            cur = conn.execute("SELECT 1 FROM teachers WHERE login = ?", (teacher_data.login,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Логин уже занят")

            hashed_password = hash_password(teacher_data.password)

            conn.execute(
                """INSERT INTO teachers (user_id, full_name, login, password, department, position)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (teacher_data.user_id, teacher_data.full_name, teacher_data.login,
                 hashed_password, teacher_data.department, teacher_data.position)
            )

            conn.execute(
                "UPDATE users SET role = 'teacher', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (teacher_data.user_id,)
            )

            conn.commit()

            logger.info(f"Зарегистрирован новый преподаватель: {teacher_data.login}")
            return {
                "user_id": teacher_data.user_id,
                "full_name": teacher_data.full_name,
                "login": teacher_data.login,
                "department": teacher_data.department,
                "position": teacher_data.position,
                "message": "Преподаватель успешно зарегистрирован"
            }

    except sqlite3.IntegrityError as e:
        logger.error(f"Ошибка целостности данных при регистрации: {e}")
        raise HTTPException(status_code=400, detail="Ошибка регистрации")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка регистрации преподавателя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")

@router.post("/teachers/login", response_model=TeacherResponse)
def login_teacher(login_data: TeacherLogin):
    """Авторизация преподавателя"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                """SELECT t.user_id, t.full_name, t.login, t.password, t.department, t.position
                   FROM teachers t
                   WHERE t.login = ?""",
                (login_data.login,)
            )

            teacher = cur.fetchone()
            if not teacher:
                raise HTTPException(status_code=404, detail="Преподаватель не найден")

            if not verify_password(login_data.password, teacher["password"]):
                raise HTTPException(status_code=401, detail="Неверный пароль")

            conn.execute(
                "UPDATE users SET role = 'teacher', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (teacher["user_id"],)
            )

            conn.commit()

            logger.info(f"Преподаватель авторизовался: {login_data.login}")
            return {
                "user_id": teacher["user_id"],
                "full_name": teacher["full_name"],
                "login": teacher["login"],
                "department": teacher["department"],
                "position": teacher["position"],
                "message": "Успешная авторизация"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка авторизации преподавателя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка авторизации")

@router.get("/teachers/{user_id}")
def get_teacher_info(user_id: str):
    """Получение информации о преподавателе"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                """SELECT t.full_name, t.login, t.department, t.position, t.created_at
                   FROM teachers t
                   WHERE t.user_id = ?""",
                (user_id,)
            )

            teacher = cur.fetchone()
            if not teacher:
                raise HTTPException(status_code=404, detail="Преподаватель не найден")

            return {
                "full_name": teacher["full_name"],
                "login": teacher["login"],
                "department": teacher["department"],
                "position": teacher["position"],
                "created_at": teacher["created_at"]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения информации о преподавателе: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения информации")

@router.get("/teachers")
def get_all_teachers():
    """Получение списка всех преподавателей"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                """SELECT t.user_id, t.full_name, t.login, t.password, t.department, t.position, t.created_at, u.role
                   FROM teachers t
                   JOIN users u ON t.user_id = u.user_id
                   ORDER BY t.created_at DESC"""
            )

            teachers = []
            for row in cur.fetchall():
                teachers.append({
                    "user_id": row["user_id"],
                    "full_name": row["full_name"],
                    "login": row["login"],
                    "password": row["password"],  # Хэшированный пароль
                    "department": row["department"],
                    "position": row["position"],
                    "created_at": row["created_at"],
                    "role": row["role"]
                })

            return teachers
    except Exception as e:
        logger.error(f"Ошибка получения списка преподавателей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка преподавателей")