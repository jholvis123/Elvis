"""
DTOs para Usuarios y Autenticación.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


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
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLoginDTO(BaseModel):
    """DTO para login de usuario."""
    
    email: EmailStr
    password: str
    # Cross-origin admin (GitHub Pages → Render): pedir tokens en el body.
    # Cookies HttpOnly siguen emitiéndose para same-origin (local/docker).
    token_in_body: bool = False


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
