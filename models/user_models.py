from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    device_info: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    created_at: str

class SettingsUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    vibration_enabled: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    language: Optional[str] = None
    font_size: Optional[str] = None

class UserRoleUpdate(BaseModel):
    user_id: str
    role: str  # 'user', 'admin', 'developer'

class UserInfo(BaseModel):
    user_id: str
    role: str
    device_info: Optional[str] = None
    created_at: str
    updated_at: str