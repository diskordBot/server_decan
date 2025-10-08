# api/__init__.py
from .users import router as users_router
from .schedule import router as schedule_router
from .groups import router as groups_router
from .health import router as health_router
from .announcements import router as announcements_router  # 👈 ДОБАВЬ

__all__ = [
    'users_router',
    'schedule_router',
    'groups_router',
    'health_router',
    'announcements_router',  # 👈 ДОБАВЬ
]
