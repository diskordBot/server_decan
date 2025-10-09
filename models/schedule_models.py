# models/schedule_models.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List


class GroupCreate(BaseModel):
    group_name: str


class LessonItem(BaseModel):
    """
    Один элемент расписания.
    """
    lesson_number: int = Field(..., ge=1)
    subject: str = ""
    teacher: str = ""
    classroom: str = ""
    type: str = ""   # 'лекц' | 'пр' | 'лб' — как свободная строка

    @validator("subject", "teacher", "classroom", "type", pre=True)
    def _strip(cls, v):
        # Нормализация строк, чтобы на сервере не было лишних пробелов/None
        return (v or "").strip()


class ScheduleData(BaseModel):
    """
    Payload для сохранения расписания группы (обе недели разом).
    Ключи словаря — русские названия дней недели.
    """
    group: str
    upper_week: Dict[str, List[LessonItem]]
    lower_week: Dict[str, List[LessonItem]]


class TeacherScheduleData(BaseModel):
    """
    Payload для сохранения расписания преподавателя (если нужно).
    """
    teacher_name: str
    upper_week: Dict[str, List[LessonItem]]
    lower_week: Dict[str, List[LessonItem]]


class TeacherScheduleResponse(BaseModel):
    """
    Ответ с расписанием преподавателя.
    """
    teacher_name: str
    upper_week: Dict[str, List[LessonItem]]
    lower_week: Dict[str, List[LessonItem]]
