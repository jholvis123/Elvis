"""
Configuración de la base de datos con SQLAlchemy.
Proporciona sesiones y el engine de conexión.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from .config import settings

# Engine de SQLAlchemy
# Configuración específica según el tipo de BD
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_recycle=3600,   # Recicla conexiones cada hora
)

# Factory de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base para modelos declarativos
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency que proporciona una sesión de base de datos.
    Se asegura de cerrar la sesión después de cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Inicializa la base de datos creando todas las tablas."""
    Base.metadata.create_all(bind=engine)
