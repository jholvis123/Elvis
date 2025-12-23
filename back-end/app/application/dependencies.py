"""
Dependencias de la capa de aplicación.
Factory functions para inyección de dependencias.
"""

from typing import Generator
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..domain.repositories.ctf_repo import CTFRepository
from ..domain.repositories.writeup_repo import WriteupRepository
from ..domain.repositories.user_repo import UserRepository
from ..domain.repositories.project_repo import ProjectRepository
from ..domain.services.ctf_service import CTFService
from ..domain.services.writeup_service import WriteupService
from ..domain.services.auth_service import AuthService
from ..domain.services.project_service import ProjectService


def get_ctf_service(ctf_repository: CTFRepository) -> CTFService:
    """Factory para CTFService."""
    return CTFService(ctf_repository)


def get_writeup_service(
    writeup_repository: WriteupRepository,
    ctf_repository: CTFRepository,
) -> WriteupService:
    """Factory para WriteupService."""
    return WriteupService(writeup_repository, ctf_repository)


def get_auth_service(user_repository: UserRepository) -> AuthService:
    """Factory para AuthService."""
    return AuthService(user_repository)


def get_project_service(project_repository: ProjectRepository) -> ProjectService:
    """Factory para ProjectService."""
    return ProjectService(project_repository)
