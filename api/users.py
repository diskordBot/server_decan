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

            # Проверяем, что ID не занят
            max_attempts = 10
            attempts = 0
            while attempts < max_attempts:
                cursor = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    break
                user_id = str(uuid.uuid4().int)[:6]
                attempts += 1

            if attempts == max_attempts:
                raise HTTPException(status_code=500, detail="Не удалось создать уникальный ID пользователя")

            # Вставляем пользователя
            conn.execute(
                "INSERT INTO users (user_id, device_info, role) VALUES (?, ?, ?)",
                (user_id, user_data.device_info, 'user')
            )

            # Создаем настройки по умолчанию
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
    """Получение списка всех зарегистрированных пользователей"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id, role, device_info, created_at, updated_at FROM users ORDER BY created_at DESC"
            )
            users = []
            for row in cursor.fetchall():
                users.append({
                    "user_id": row['user_id'],
                    "role": row['role'],
                    "device_info": row['device_info'],
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at']
                })
            return users
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка пользователей")


@router.get("/users/{user_id}/role")
def get_user_role(user_id: str):
    """Получение роли пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT role FROM users WHERE user_id = ?",
                (user_id,)
            )
            user = cursor.fetchone()

            if not user:
                # Если пользователь не существует, создаем его с ролью по умолчанию
                try:
                    conn.execute(
                        "INSERT INTO users (user_id, role) VALUES (?, ?)",
                        (user_id, 'user')
                    )
                    conn.execute(
                        "INSERT INTO user_settings (user_id) VALUES (?)",
                        (user_id,)
                    )
                    conn.commit()
                    logger.info(f"Создан новый пользователь: {user_id}")
                    return {"role": "user"}
                except sqlite3.IntegrityError:
                    # Возможно, пользователь был создан в параллельном запросе
                    cursor = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
                    user = cursor.fetchone()
                    if user:
                        return {"role": user['role']}
                    return {"role": "user"}

            return {"role": user['role']}

    except Exception as e:
        logger.error(f"Ошибка получения роли пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения роли пользователя")


@router.put("/users/role")
def update_user_role(role_data: UserRoleUpdate):
    """Обновление роли пользователя (только для разработчиков)"""
    try:
        with get_db_connection() as conn:
            # Проверяем, что роль валидна
            if role_data.role not in ['user', 'admin', 'developer']:
                raise HTTPException(status_code=400, detail="Неверная роль пользователя")

            # Проверяем существование пользователя
            cursor = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (role_data.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            # Не позволяем снять права разработчика с самого себя
            if role_data.user_id == '000000' and role_data.role != 'developer':
                raise HTTPException(status_code=400, detail="Нельзя изменить роль системного разработчика")

            # Обновляем роль пользователя
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
    """Снятие прав администратора с пользователя (только для разработчиков)"""
    try:
        with get_db_connection() as conn:
            # Проверяем существование пользователя
            cursor = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            if user['role'] != 'admin':
                raise HTTPException(status_code=400, detail="Пользователь не является администратором")

            # Не позволяем снять права с системного разработчика
            if user_id == '000000':
                raise HTTPException(status_code=400, detail="Нельзя изменить роль системного разработчика")

            # Понижаем до обычного пользователя
            conn.execute(
                "UPDATE users SET role = 'user', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )

            conn.commit()
            logger.info(f"Пользователь {user_id} понижен до обычного пользователя")
            return {"message": "Права администратора успешно сняты"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка снятия прав администратора: {e}")
        raise HTTPException(status_code=500, detail="Ошибка снятия прав администратора")


@router.get("/users/{user_id}/settings")
def get_user_settings(user_id: str):
    """Получение настроек пользователя"""
    try:
        with get_db_connection() as conn:
            # Сначала проверяем существование пользователя
            cursor = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                # Если пользователь не существует, создаем его с настройками по умолчанию
                try:
                    conn.execute("INSERT INTO users (user_id, role) VALUES (?, ?)", (user_id, 'user'))
                    conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
                    conn.commit()
                    logger.info(f"Создан новый пользователь: {user_id}")
                except sqlite3.IntegrityError:
                    pass  # Пользователь мог быть создан в параллельном запросе

            # Получаем настройки
            cursor = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
            settings = cursor.fetchone()

            if not settings:
                # Если настроек нет, создаем их
                conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
                conn.commit()
                cursor = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
                settings = cursor.fetchone()

            return {
                "notifications_enabled": bool(settings['notifications_enabled']),
                "vibration_enabled": bool(settings['vibration_enabled']),
                "sound_enabled": bool(settings['sound_enabled']),
                "language": settings['language'],
                "font_size": settings['font_size']
            }

    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")


@router.put("/users/{user_id}/settings")
def update_user_settings(user_id: str, settings: SettingsUpdate):
    """Обновление настроек пользователя"""
    try:
        with get_db_connection() as conn:
            # Проверяем существование пользователя
            cursor = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                # Если пользователь не существует, создаем его
                conn.execute("INSERT INTO users (user_id, role) VALUES (?, ?)", (user_id, 'user'))
                conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
                logger.info(f"Создан новый пользователь: {user_id}")

            # Строим динамический запрос для обновления
            update_fields = []
            update_values = []

            if settings.notifications_enabled is not None:
                update_fields.append("notifications_enabled = ?")
                update_values.append(int(settings.notifications_enabled))

            if settings.vibration_enabled is not None:
                update_fields.append("vibration_enabled = ?")
                update_values.append(int(settings.vibration_enabled))

            if settings.sound_enabled is not None:
                update_fields.append("sound_enabled = ?")
                update_values.append(int(settings.sound_enabled))

            if settings.language is not None:
                update_fields.append("language = ?")
                update_values.append(settings.language)

            if settings.font_size is not None:
                update_fields.append("font_size = ?")
                update_values.append(settings.font_size)

            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(user_id)

                query = f"UPDATE user_settings SET {', '.join(update_fields)} WHERE user_id = ?"
                conn.execute(query, update_values)
                conn.commit()

            logger.info(f"Настройки пользователя {user_id} обновлены")
            return {"message": "Настройки успешно обновлены"}

    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настроек: {str(e)}")