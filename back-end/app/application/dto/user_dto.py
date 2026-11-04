"""
DTOs para Usuarios y Autenticación.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator

# Alias de jugador: 3-30 caracteres, letras, números, guion y guion bajo.
PLAYER_ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
# Alias que podrían hacerse pasar por el dueño o el sistema (comparación sin mayúsculas).
RESERVED_ALIASES = frozenset(
    {"admin", "administrator", "administrador", "root", "owner", "system", "sistema",
     "moderator", "moderador", "support", "soporte", "elvis", "jholvis123"}
)


class UserCreateDTO(BaseModel):
    """DTO para crear un usuario."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123"
            }
        }


class UserResponseDTO(BaseModel):
    """DTO para respuesta de usuario."""
    
    id: UUID
    email: Optional[str] = None
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLoginDTO(BaseModel):
    """DTO para login de usuario: por email (admin) o por alias (jugador)."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    password: str
    # Cross-origin admin (GitHub Pages → Render): pedir tokens en el body.
    # Cookies HttpOnly siguen emitiéndose para same-origin (local/docker).
    token_in_body: bool = False

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.email and not self.username:
            raise ValueError("email or username is required")
        return self


class PlayerRegisterDTO(BaseModel):
    """Registro de jugador del CTF: solo alias + contraseña (sin email)."""

    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt usa 72 bytes

    @field_validator("username")
    @classmethod
    def validate_alias(cls, v: str) -> str:
        v = v.strip()
        if not PLAYER_ALIAS_RE.match(v):
            raise ValueError("alias: 3-30 caracteres, solo letras, números, - y _")
        if v.lower() in RESERVED_ALIASES:
            raise ValueError("alias reservado")
        return v


class TokenDTO(BaseModel):
    """DTO para tokens de autenticación."""
    
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"  # noqa: S105 — OAuth token_type value
    expires_in: int  # Segundos hasta expiración


class TokenPayloadDTO(BaseModel):
    """DTO para el payload del token JWT."""
    
    sub: str  # User ID
    exp: datetime
    iat: datetime
    type: str  # "access" o "refresh"


class PasswordChangeDTO(BaseModel):
    """DTO para cambio de contraseña."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class AuthStatusDTO(BaseModel):
    """
    DTO para respuesta de estado de autenticación (login/refresh).

    Por defecto los JWT van en cookies HttpOnly (sin tokens en body).
    Con `token_in_body=true` en la petición, también se incluyen
    access_token / refresh_token para clientes Bearer (Pages cross-origin).
    Login/refresh usan response_model_exclude_none: sin token_in_body no
    aparecen keys null en el JSON.
    """
    
    authenticated: bool
    user: Optional[UserResponseDTO] = None
    expires_in: Optional[int] = None  # Segundos hasta expiración del access token
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None  # noqa: S105 — OAuth token_type when Bearer body mode
    
    class Config:
        json_schema_extra = {
            "example": {
                "authenticated": True,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-01T00:00:00"
                },
                "expires_in": 1800
            }
        }


class RefreshRequestDTO(BaseModel):
    """Refresh opcional vía body (Bearer / Pages). Cookie refresh sigue válida."""

    refresh_token: Optional[str] = None
    token_in_body: bool = False
