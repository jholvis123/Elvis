"""
Core module - Infraestructura base del sistema.
Contiene configuración, base de datos, seguridad y logging.
"""

from .config import settings
from .database import get_db, engine, SessionLocal
from .security import get_password_hash, verify_password
from .logging import logger

__all__ = [
    "settings",
    "get_db",
    "engine",
    "SessionLocal",
    "get_password_hash",
    "verify_password",
    "logger",
]
