# models/teacher_models.py
from pydantic import BaseModel, Field
from typing import Optional

class TeacherCreate(BaseModel):
    user_id: str
    full_name: str = Field(..., min_length=3, max_length=100)
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)

class TeacherLogin(BaseModel):
    login: str
    password: str

class TeacherResponse(BaseModel):
    user_id: str
    full_name: str
    login: str
    department: Optional[str] = None
    position: Optional[str] = None
    message: str

class TeacherInfo(BaseModel):
    full_name: str
    login: str
    department: Optional[str] = None
    position: Optional[str] = None
    created_at: str