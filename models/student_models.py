# models/student_models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class StudentCreate(BaseModel):
    user_id: str
    full_name: str = Field(..., min_length=3, max_length=100)
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    group_name: str

class StudentLogin(BaseModel):
    login: str
    password: str

class StudentResponse(BaseModel):
    user_id: str
    full_name: str
    login: str
    group_name: str
    message: str

class StudentInfo(BaseModel):
    full_name: str
    login: str
    group_name: str
    created_at: str
