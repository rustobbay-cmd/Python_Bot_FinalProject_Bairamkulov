"""
Обработчики бота.

Регистрация всех роутеров.
"""

from aiogram import Router

from .start import router as start_router
from .ad_create import router as ad_create_router
from .ad_search import router as ad_search_router
from .ad_manage import router as ad_manage_router
from .moderation import router as moderation_router
from .feedback import router as feedback_router
from .notifications import router as notifications_router
from .admin import router as admin_router


def get_all_routers() -> list[Router]:
    """Возвращает список всех роутеров для регистрации."""
    return [
        start_router,
        ad_create_router,
        ad_search_router,
        ad_manage_router,
        moderation_router,
        feedback_router,
        notifications_router,
        admin_router,
    ]


__all__ = [
    "get_all_routers",
    "start_router",
    "ad_create_router",
    "ad_search_router",
    "ad_manage_router",
    "moderation_router",
    "feedback_router",
    "notifications_router",
    "admin_router",
]