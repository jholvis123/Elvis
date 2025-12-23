"""
Configuración compartida para tests.
"""

import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..core.database import Base
from ..core.config import settings


# Base de datos en memoria para tests
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Fixture que proporciona una sesión de BD limpia para cada test."""
    # Crear tablas
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Limpiar después del test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session):
    """Fixture que proporciona un cliente de test para la API."""
    from fastapi.testclient import TestClient
    from ..main import app
    from ..core.database import get_db
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()
