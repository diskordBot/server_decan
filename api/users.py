from fastapi import APIRouter, HTTPException
import sqlite3
import uuid
from datetime import datetime
from database.connection import get_db_connection
from utils.logger import logger
from models.user_models import UserCreate, UserResponse, SettingsUpdate, UserRoleUpdate, UserInfo

router = APIRouter()


@router.post("/users", response_model=UserResponse)
def create_user(user_data: UserCreate):
    """Создание нового пользователя"""
    try:
        with get_db_connection() as conn:
            user_id = str(uuid.uuid4().int)[:6]

            for _ in range(10):
                cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
                if not cur.fetchone():
                    break
                user_id = str(uuid.uuid4().int)[:6]
            else:
                raise HTTPException(status_code=500, detail="Не удалось создать уникальный ID пользователя")

            conn.execute(
                "INSERT INTO users (user_id, device_info, role) VALUES (?, ?, 'user')",
                (user_id, user_data.device_info)
            )
            conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
            conn.commit()

            logger.info(f"Создан новый пользователь: {user_id}")
            return {"user_id": user_id, "created_at": datetime.now().isoformat()}

    except sqlite3.IntegrityError as e:
        logger.error(f"Ошибка целостности данных: {e}")
        raise HTTPException(status_code=400, detail="Ошибка создания пользователя")
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания пользователя")


@router.get("/users", response_model=list[UserInfo])
def get_all_users():
    """Список всех пользователей с полной информацией"""
    try:
        with get_db_connection() as conn:
            # Получаем всех пользователей с LEFT JOIN к students и teachers
            cur = conn.execute("""
                SELECT 
                    u.user_id, 
                    u.role, 
                    u.device_info, 
                    u.created_at, 
                    u.updated_at,
                    s.full_name as student_full_name,
                    s.login as student_login,
                    s.password as student_password,
                    s.group_name as student_group,
                    t.full_name as teacher_full_name,
                    t.login as teacher_login,
                    t.password as teacher_password,
                    t.department as teacher_department,
                    t.position as teacher_position
                FROM users u
                LEFT JOIN students s ON u.user_id = s.user_id
                LEFT JOIN teachers t ON u.user_id = t.user_id
                ORDER BY u.created_at DESC
            """)

            users = []
            for row in cur.fetchall():
                user_info = {
                    "user_id": row["user_id"],
                    "role": row["role"] or "user",
                    "device_info": row["device_info"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"] or datetime.now().isoformat()
                }

                # Добавляем информацию о студенте, если есть
                if row["student_full_name"]:
                    user_info.update({
                        "full_name": row["student_full_name"],
                        "login": row["student_login"],
                        "password": row["student_password"],
                        "group_name": row["student_group"]
                    })

                # Добавляем информацию о преподавателе, если есть
                elif row["teacher_full_name"]:
                    user_info.update({
                        "full_name": row["teacher_full_name"],
                        "login": row["teacher_login"],
                        "password": row["teacher_password"],
                        "department": row["teacher_department"],
                        "position": row["teacher_position"]
                    })

                users.append(user_info)

            logger.info(f"Получено {len(users)} пользователей с полной информацией")
            return users

    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка пользователей")


@router.get("/users/{user_id}/role")
def get_user_role(user_id: str):
    """Получение роли пользователя (если нет — создаём как 'user')"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()

            if not row:
                try:
                    conn.execute("INSERT INTO users (user_id, role) VALUES (?, 'user')", (user_id,))
                    conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
                    conn.commit()
                    logger.info(f"Создан новый пользователь: {user_id}")
                    return {"role": "user"}
                except sqlite3.IntegrityError:
                    cur2 = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
                    row2 = cur2.fetchone()
                    return {"role": (row2["role"] if row2 else "user")}

            return {"role": row["role"]}

    except Exception as e:
        logger.error(f"Ошибка получения роли пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения роли пользователя")


@router.put("/users/role")
def update_user_role(role_data: UserRoleUpdate):
    """Изменение роли пользователя"""
    try:
        if role_data.role not in ["user", "admin", "developer", "teacher", "student"]:
            raise HTTPException(status_code=400, detail="Неверная роль пользователя")

        with get_db_connection() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (role_data.user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            if role_data.user_id == "000000" and role_data.role != "developer":
                raise HTTPException(status_code=400, detail="Нельзя изменить роль системного разработчика")

            conn.execute(
                "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (role_data.role, role_data.user_id)
            )
            conn.commit()
            logger.info(f"Роль пользователя {role_data.user_id} изменена на {role_data.role}")
            return {"message": "Роль пользователя успешно обновлена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления роли пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления роли пользователя")


@router.delete("/users/{user_id}/admin")
def remove_admin_role(user_id: str):
    """Снятие прав администратора"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            if row["role"] != "admin":
                raise HTTPException(status_code=400, detail="Пользователь не является администратором")
            if user_id == "000000":
                raise HTTPException(status_code=400, detail="Нельзя изменить роль системного разработчика")

            conn.execute(
                "UPDATE users SET role = 'user', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            logger.info(f"Пользователь {user_id} понижен до user")
            return {"message": "Права администратора успешно сняты"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка снятия прав администратора: {e}")
        raise HTTPException(status_code=500, detail="Ошибка снятия прав администратора")


@router.get("/users/{user_id}/settings")
def get_user_settings(user_id: str):
    """Загрузка настроек; если нет — создаём дефолтные"""
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if not cur.fetchone():
                conn.execute("INSERT INTO users (user_id, role) VALUES (?, 'user')", (user_id,))
                conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
                conn.commit()

            cur = conn.execute("""
                SELECT notifications_enabled, vibration_enabled, sound_enabled, language, font_size
                FROM user_settings WHERE user_id = ?
            """, (user_id,))
            row = cur.fetchone()
            if not row:
                conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
                conn.commit()
                return {
                    "notifications_enabled": True,
                    "vibration_enabled": True,
                    "sound_enabled": True,
                    "language": "Русский",
                    "font_size": "Средний",
                }

            return {
                "notifications_enabled": bool(row["notifications_enabled"]),
                "vibration_enabled": bool(row["vibration_enabled"]),
                "sound_enabled": bool(row["sound_enabled"]),
                "language": row["language"],
                "font_size": row["font_size"],
            }
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек пользователя")


@router.put("/users/{user_id}/settings")
def update_user_settings(user_id: str, data: SettingsUpdate):
    """Частичное обновление настроек"""
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))

            fields = []
            values = []
            if data.notifications_enabled is not None:
                fields.append("notifications_enabled = ?")
                values.append(1 if data.notifications_enabled else 0)
            if data.vibration_enabled is not None:
                fields.append("vibration_enabled = ?")
                values.append(1 if data.vibration_enabled else 0)
            if data.sound_enabled is not None:
                fields.append("sound_enabled = ?")
                values.append(1 if data.sound_enabled else 0)
            if data.language is not None:
                fields.append("language = ?")
                values.append(data.language)
            if data.font_size is not None:
                fields.append("font_size = ?")
                values.append(data.font_size)

            if fields:
                set_clause = ", ".join(fields + ["updated_at = CURRENT_TIMESTAMP"])
                conn.execute(f"UPDATE user_settings SET {set_clause} WHERE user_id = ?", (*values, user_id))
                conn.commit()

            return {"message": "Настройки обновлены"}
    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления настроек пользователя")
