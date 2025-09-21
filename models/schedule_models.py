from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class GroupCreate(BaseModel):
    group_name: str

class ScheduleData(BaseModel):
    group: str
    upper_week: Dict[str, List[Dict[str, Any]]]
    lower_week: Dict[str, List[Dict[str, Any]]]

class TeacherScheduleData(BaseModel):
    teacher_name: str
    upper_week: Dict[str, List[Dict[str, Any]]]
    lower_week: Dict[str, List[Dict[str, Any]]]

class TeacherScheduleResponse(BaseModel):
    teacher_name: str
    upper_week: Dict[str, List[Dict[str, Any]]]
    lower_week: Dict[str, List[Dict[str, Any]]]