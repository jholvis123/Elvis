"""
Configuración compartida para tests.
"""

import pytest
from typing import Generator
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..infrastructure.persistence.base import Base
from ..infrastructure.persistence.models import (  # noqa: F401 - register metadata
    UserModel,
    ProjectModel,
    CTFModel,
    WriteupModel,
    AttachmentModel,
    ContactModel,
    FlagSubmissionModel,
)


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


def _auth_headers(db: Session, *, email: str, username: str, is_admin: bool) -> dict:
    from ..core.security import get_password_hash
    from ..infrastructure.security.jwt_provider import JWTProvider

    uid = str(uuid4())
    user = UserModel(
        id=uid,
        email=email,
        username=username,
        hashed_password=get_password_hash("securepassword123"),
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    token = JWTProvider().create_access_token(uid)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db: Session) -> dict:
    """Headers Bearer de un usuario administrador."""
    return _auth_headers(
        db, email="admin@example.com", username="adminuser", is_admin=True
    )


@pytest.fixture
def user_headers(db: Session) -> dict:
    """Headers Bearer de un usuario no administrador."""
    return _auth_headers(
        db, email="user@example.com", username="regularuser", is_admin=False
    )
