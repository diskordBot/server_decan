# api/students.py
from fastapi import APIRouter, HTTPException
import sqlite3
from database.connection import get_db_connection
from utils.logger import logger
from models.student_models import StudentCreate, StudentLogin, StudentResponse
from data.groups import DEFAULT_GROUPS, get_group_info
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

def is_valid_group(group_name: str) -> bool:
    """Проверяет, является ли группа допустимой"""
    return group_name in DEFAULT_GROUPS

@router.post("/students/register", response_model=StudentResponse)
def register_student(student_data: StudentCreate):
    """Регистрация нового студента"""
    try:
        if not is_valid_group(student_data.group_name):
            raise HTTPException(
                status_code=400,
                detail=f"Группа '{student_data.group_name}' не существует. Доступные группы: {DEFAULT_GROUPS}"
            )

        with get_db_connection() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (student_data.user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            cur = conn.execute("SELECT 1 FROM students WHERE login = ?", (student_data.login,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Логин уже занят")

            cur = conn.execute("SELECT 1 FROM schedule_groups WHERE group_name = ?", (student_data.group_name,))
            if not cur.fetchone():
                conn.execute(
                    "INSERT OR IGNORE INTO schedule_groups (group_name) VALUES (?)",
                    (student_data.group_name,)
                )
                logger.info(f"Автоматически создана группа: {student_data.group_name}")

            hashed_password = hash_password(student_data.password)

            conn.execute(
                """INSERT INTO students (user_id, full_name, login, password, group_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_data.user_id, student_data.full_name, student_data.login,
                 hashed_password, student_data.group_name)
            )

            conn.execute(
                "UPDATE users SET role = 'student', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (student_data.user_id,)
            )

            conn.commit()

            group_info = get_group_info(student_data.group_name)
            logger.info(
                f"Зарегистрирован новый студент: {student_data.login} в группе {student_data.group_name}")

            return {
                "user_id": student_data.user_id,
                "full_name": student_data.full_name,
                "login": student_data.login,
                "group_name": student_data.group_name,
                "group_info": group_info,
                "message": "Студент успешно зарегистрирован"
            }

    except sqlite3.IntegrityError as e:
        logger.error(f"Ошибка целостности данных при регистрации: {e}")
        raise HTTPException(status_code=400, detail="Ошибка регистрации")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка регистрации студента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")

@router.post("/students/login", response_model=StudentResponse)
def login_student(login_data: StudentLogin):
    """Авторизация студента"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                """SELECT s.user_id, s.full_name, s.login, s.password, s.group_name, u.role
                   FROM students s
                   JOIN users u ON s.user_id = u.user_id
                   WHERE s.login = ?""",
                (login_data.login,)
            )

            student = cur.fetchone()
            if not student:
                raise HTTPException(status_code=404, detail="Студент не найден")

            if not verify_password(login_data.password, student["password"]):
                raise HTTPException(status_code=401, detail="Неверный пароль")

            conn.execute(
                "UPDATE users SET role = 'student', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (student["user_id"],)
            )

            conn.commit()

            group_info = get_group_info(student["group_name"])
            logger.info(f"Студент авторизовался: {login_data.login} (группа: {student['group_name']})")
            return {
                "user_id": student["user_id"],
                "full_name": student["full_name"],
                "login": student["login"],
                "group_name": student["group_name"],
                "group_info": group_info,
                "message": "Успешная авторизация"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка авторизации студента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка авторизации")

@router.get("/students/{user_id}")
def get_student_info(user_id: str):
    """Получение информации о студенте"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                """SELECT s.full_name, s.login, s.group_name, s.created_at
                   FROM students s
                   WHERE s.user_id = ?""",
                (user_id,)
            )

            student = cur.fetchone()
            if not student:
                raise HTTPException(status_code=404, detail="Студент не найден")

            group_info = get_group_info(student["group_name"])

            return {
                "full_name": student["full_name"],
                "login": student["login"],
                "group_name": student["group_name"],
                "group_info": group_info,
                "created_at": student["created_at"]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения информации о студенте: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения информации")

@router.get("/students")
def get_all_students():
    """Получение списка всех студентов с информацией"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                """SELECT s.user_id, s.full_name, s.login, s.password, s.group_name, s.created_at, u.role
                   FROM students s
                   JOIN users u ON s.user_id = u.user_id
                   ORDER BY s.created_at DESC"""
            )

            students = []
            for row in cur.fetchall():
                logger.info(f"DEBUG: Student data: {row}")  # Логирование полученных данных
                students.append({
                    "user_id": row["user_id"],
                    "full_name": row["full_name"],
                    "login": row["login"],
                    "password": row["password"],  # Хэшированный пароль
                    "group_name": row["group_name"],
                    "created_at": row["created_at"],
                    "role": row["role"]
                })

            return students
    except Exception as e:
        logger.error(f"Ошибка получения списка студентов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка студентов")
