"""
Модуль базы данных.

Экспортирует основные компоненты для работы с БД.
"""

from .database import db, Base, get_session, Database
from .models import (
    User, Ad, Feedback, Report, Subscription,
    AdStatus, FeedbackType, ReportReason, ReportStatus,
    AD_CATEGORIES, REPORT_REASONS_DISPLAY
)

__all__ = [
    # Database
    "db",
    "Base",
    "get_session",
    "Database",
    # Models
    "User",
    "Ad", 
    "Feedback",
    "Report",
    "Subscription",
    # Enums
    "AdStatus",
    "FeedbackType",
    "ReportReason",
    "ReportStatus",
    # Constants
    "AD_CATEGORIES",
    "REPORT_REASONS_DISPLAY",
]