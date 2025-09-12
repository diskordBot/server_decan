from .users import router as users_router
from .schedule import router as schedule_router
from .groups import router as groups_router
from .health import router as health_router

__all__ = [
    'users_router',
    'schedule_router',
    'groups_router',
    'health_router'
]