# handlers/__init__.py
from .common_handlers import router as common_router
from .guide_handlers import router as guide_router
from .traveler_handlers import router as traveler_router
from .admin_handlers import router as admin_router

# Экспортируем роутеры для использования в main.py
__all__ = ["common_router", "guide_router", "traveler_router", "admin_router"]
