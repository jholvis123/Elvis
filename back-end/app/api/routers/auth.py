"""
Router de autenticación.
Implementa autenticación segura con cookies HttpOnly.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...application.dto.user_dto import (
    UserCreateDTO,
    UserResponseDTO,
    UserLoginDTO,
    TokenDTO,
    AuthStatusDTO,
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
    get_cookie_service,
    get_csrf_service,
)
from ...infrastructure.security.jwt_provider import JWTProvider
from ...infrastructure.security.cookie_service import CookieService
from ...infrastructure.security.csrf_service import CSRFService

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


@router.post("/login", response_model=AuthStatusDTO)
@limiter.limit("10/minute")  # Limitar intentos de login a 10 por minuto por IP
async def login(
    request: Request,
    response: Response,
    data: UserLoginDTO,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    cookie_service: CookieService = Depends(get_cookie_service),
    csrf_service: CSRFService = Depends(get_csrf_service),
):
    """
    Inicia sesión y establece cookies seguras.
    
    - Los tokens se almacenan en cookies HttpOnly (no accesibles desde JavaScript)
    - Se genera un token CSRF para protección adicional
    """
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
    csrf_token = csrf_service.generate_token(str(user.id))
    
    # Establecer cookies seguras
    cookie_service.set_access_token_cookie(response, access_token)
    cookie_service.set_refresh_token_cookie(response, refresh_token)
    cookie_service.set_csrf_token_cookie(response, csrf_token)
    
    # Retornar solo información del usuario (sin tokens en body)
    return AuthStatusDTO(
        authenticated=True,
        user=UserResponseDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=AuthStatusDTO)
async def refresh_token(
    request: Request,
    response: Response,
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    user_repo: UserRepository = Depends(get_user_repository),
    cookie_service: CookieService = Depends(get_cookie_service),
    csrf_service: CSRFService = Depends(get_csrf_service),
):
    """
    Refresca el access token usando el refresh token de la cookie.
    """
    # Obtener refresh token de la cookie
    refresh_token_value = cookie_service.get_refresh_token_from_cookie(request)
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    
    token_data = jwt_provider.verify_refresh_token(refresh_token_value)
    
    if not token_data:
        # Limpiar cookies si el token es inválido
        cookie_service.clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Verificar que el usuario existe
    from uuid import UUID
    user = user_repo.get_by_id(UUID(token_data.user_id))
    
    if not user or not user.is_active:
        cookie_service.clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Generar nuevo access token y CSRF token
    access_token = jwt_provider.create_access_token(str(user.id))
    csrf_token = csrf_service.generate_token(str(user.id))
    
    # Actualizar cookies
    cookie_service.set_access_token_cookie(response, access_token)
    cookie_service.set_csrf_token_cookie(response, csrf_token)
    
    return AuthStatusDTO(
        authenticated=True,
        user=UserResponseDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    response: Response,
    cookie_service: CookieService = Depends(get_cookie_service),
):
    """
    Cierra sesión eliminando las cookies de autenticación.
    """
    cookie_service.clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


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
