"""
Router de autenticación.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...application.dto.user_dto import (
    UserCreateDTO,
    UserResponseDTO,
    UserLoginDTO,
    TokenDTO,
)
from ...core.database import get_db
from ...core.security import get_password_hash, verify_password
from ...core.config import settings
from ...domain.entities.user import User
from ...domain.repositories.user_repo import UserRepository
from ...domain.services.auth_service import AuthService
from ..dependencies import (
    get_user_repository,
    get_auth_service,
    get_jwt_provider,
    get_current_user,
)
from ...infrastructure.security.jwt_provider import JWTProvider

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Limitar registros a 5 por hora por IP
async def register(
    request: Request,
    data: UserCreateDTO,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Registra un nuevo usuario."""
    # Validar datos
    errors = auth_service.validate_registration(data.email, data.username)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors,
        )
    
    # Crear usuario
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=get_password_hash(data.password),
    )
    
    saved_user = user_repo.save(user)
    
    return UserResponseDTO(
        id=saved_user.id,
        email=saved_user.email,
        username=saved_user.username,
        is_active=saved_user.is_active,
        is_admin=saved_user.is_admin,
        created_at=saved_user.created_at,
    )


@router.post("/login", response_model=TokenDTO)
@limiter.limit("10/minute")  # Limitar intentos de login a 10 por minuto por IP
async def login(
    request: Request,
    data: UserLoginDTO,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
):
    """Inicia sesión y retorna tokens."""
    # Buscar usuario
    user = user_repo.get_by_email(data.email)
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not auth_service.can_login(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Generar tokens
    access_token = jwt_provider.create_access_token(str(user.id))
    refresh_token = jwt_provider.create_refresh_token(str(user.id))
    
    return TokenDTO(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenDTO)
async def refresh_token(
    refresh_token: str,
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Refresca el token de acceso."""
    token_data = jwt_provider.verify_refresh_token(refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Verificar que el usuario existe
    from uuid import UUID
    user = user_repo.get_by_id(UUID(token_data.user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Generar nuevo access token
    access_token = jwt_provider.create_access_token(str(user.id))
    
    return TokenDTO(
        access_token=access_token,
        refresh_token=refresh_token,  # Mantener el mismo refresh token
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponseDTO)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Obtiene el perfil del usuario autenticado."""
    return UserResponseDTO(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )
