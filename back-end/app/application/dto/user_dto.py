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


class TokenDTO(BaseModel):
    """DTO para tokens de autenticación."""
    
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
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
