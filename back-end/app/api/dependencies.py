"""
Dependencias de la capa API.
Inyección de dependencias para FastAPI.
"""

from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..domain.entities.user import User
from ..domain.repositories.ctf_repo import CTFRepository
from ..domain.repositories.writeup_repo import WriteupRepository
from ..domain.repositories.user_repo import UserRepository
from ..domain.repositories.project_repo import ProjectRepository
from ..domain.repositories.attachment_repo import AttachmentRepository
from ..domain.repositories.contact_repo import ContactRepository
from ..domain.repositories.flag_submission_repo import FlagSubmissionRepository
from ..domain.repositories.portfolio_repo import PortfolioRepository
from ..domain.services.ctf_service import CTFService
from ..domain.services.writeup_service import WriteupService
from ..domain.services.auth_service import AuthService
from ..domain.services.project_service import ProjectService
from ..domain.services.flag_service import FlagService
from ..domain.services.contact_service import ContactService
from ..domain.services.attachment_service import AttachmentService
from ..domain.services.portfolio_service import PortfolioService
from ..infrastructure.persistence.repositories import (
    CTFSqlRepository,
    WriteupSqlRepository,
    UserSqlRepository,
    ProjectSqlRepository,
    AttachmentSqlRepository,
    ContactSqlRepository,
    FlagSubmissionSqlRepository,
    PortfolioSqlRepository,
)
from ..infrastructure.storage.local_storage import FileSystemStorage
from ..domain.services.storage_service import StorageService
from ..infrastructure.security.jwt_provider import JWTProvider
from ..infrastructure.security.cookie_service import CookieService, cookie_service
from ..infrastructure.security.csrf_service import CSRFService, csrf_service

# Security scheme - mantener para compatibilidad con Bearer tokens (API externa)
security = HTTPBearer(auto_error=False)


# Cookie and CSRF service dependencies
def get_cookie_service() -> CookieService:
    """Obtiene el servicio de cookies."""
    return cookie_service


def get_csrf_service() -> CSRFService:
    """Obtiene el servicio CSRF."""
    return csrf_service


# Repository dependencies
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Obtiene el repositorio de usuarios."""
    return UserSqlRepository(db)


def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    """Obtiene el repositorio de proyectos."""
    return ProjectSqlRepository(db)


def get_ctf_repository(db: Session = Depends(get_db)) -> CTFRepository:
    """Obtiene el repositorio de CTFs."""
    return CTFSqlRepository(db)


def get_writeup_repository(db: Session = Depends(get_db)) -> WriteupRepository:
    """Obtiene el repositorio de writeups."""
    return WriteupSqlRepository(db)


def get_attachment_repository(db: Session = Depends(get_db)) -> AttachmentRepository:
    """Obtiene el repositorio de attachments."""
    return AttachmentSqlRepository(db)


def get_contact_repository(db: Session = Depends(get_db)) -> ContactRepository:
    """Obtiene el repositorio de contacts."""
    return ContactSqlRepository(db)


def get_flag_submission_repository(db: Session = Depends(get_db)) -> FlagSubmissionRepository:
    """Obtiene el repositorio de flag submissions."""
    return FlagSubmissionSqlRepository(db)


# Service dependencies
def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Obtiene el servicio de autenticación."""
    return AuthService(user_repo)


def get_ctf_service(
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
) -> CTFService:
    """Obtiene el servicio de CTF."""
    return CTFService(ctf_repo)


def get_writeup_service(
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
) -> WriteupService:
    """Obtiene el servicio de writeups."""
    return WriteupService(writeup_repo, ctf_repo)


def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> ProjectService:
    """Obtiene el servicio de proyectos."""
    return ProjectService(project_repo)


def get_flag_service(
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    flag_submission_repo: FlagSubmissionRepository = Depends(get_flag_submission_repository),
) -> FlagService:
    """Obtiene el servicio de flags."""
    return FlagService(ctf_repo, flag_submission_repo)


def get_contact_service(
    contact_repo: ContactRepository = Depends(get_contact_repository),
) -> ContactService:
    """Obtiene el servicio de contacto."""
    return ContactService(contact_repo)


def get_attachment_service(
    attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
) -> AttachmentService:
    """Obtiene el servicio de attachments."""
    return AttachmentService(attachment_repo)


def get_portfolio_repository(db: Session = Depends(get_db)) -> PortfolioRepository:
    """Obtiene el repositorio de perfil de portfolio."""
    return PortfolioSqlRepository(db)


def get_portfolio_service(
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> PortfolioService:
    """Obtiene el servicio de portfolio (persistido, con fallback a DEFAULT_PROFILE)."""
    return PortfolioService(portfolio_repo)


# JWT Provider
def get_jwt_provider() -> JWTProvider:
    """Obtiene el proveedor de JWT."""
    return JWTProvider()


# Storage dependencies
def get_storage_service() -> StorageService:
    """Always local filesystem — attachments/writeups depend on upload_dir + /uploads paths."""
    return FileSystemStorage()


def get_avatar_storage_service() -> StorageService:
    """Avatar-only storage: S3/R2 when STORAGE_TYPE=s3, otherwise local filesystem."""
    from ..core.config import settings

    storage_type = (settings.STORAGE_TYPE or "local").strip().lower()
    if storage_type == "s3":
        from ..infrastructure.storage.s3_storage import S3Storage

        return S3Storage()

    return FileSystemStorage()


# Auth dependencies
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Obtiene el usuario actual desde el token JWT.
    
    Soporta dos métodos de autenticación:
    1. Cookie HttpOnly (preferido para navegadores)
    2. Bearer token en header (para APIs externas/móviles)
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe.
    """
    # If client sent Authorization: Bearer ... (even empty), do NOT fall back to cookie.
    # Empty/invalid Bearer → 401 (prevents CSRF bypass via "Bearer " + cookie session).
    auth_header = request.headers.get("Authorization") or ""
    auth_lower = auth_header.lower()
    bearer_attempted = auth_lower.startswith("bearer")
    token: Optional[str] = None
    if bearer_attempted:
        # credentials.credentials may be "" for "Bearer " / "Bearer"
        if credentials and credentials.credentials:
            token = credentials.credentials.strip() or None
        elif auth_lower.startswith("bearer "):
            token = auth_header[7:].strip() or None
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # Cookie HttpOnly (same-origin local/docker)
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = jwt_provider.verify_access_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_repo.get_by_id(UUID(token_data.user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Optional[User]:
    """
    Obtiene el usuario actual si está autenticado, None si no.
    Soporta tanto cookies como Bearer tokens.
    """
    auth_header = request.headers.get("Authorization") or ""
    bearer_attempted = auth_header.lower().startswith("bearer")
    if bearer_attempted:
        # Delegate to get_current_user (no cookie fallback; may 401 → None)
        try:
            return await get_current_user(request, credentials, jwt_provider, user_repo)
        except HTTPException:
            return None
    if not request.cookies.get("access_token"):
        return None
    try:
        return await get_current_user(request, credentials, jwt_provider, user_repo)
    except HTTPException:
        return None


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verifica que el usuario actual sea administrador.
    
    Raises:
        HTTPException: Si el usuario no es admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user
