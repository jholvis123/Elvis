"""
DTOs para Contact.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


class ContactCreateDTO(BaseModel):
    """DTO para crear un mensaje de contacto."""
    
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    project_type: str = Field(..., description="web, security, ctf, other")
    message: str = Field(..., min_length=10, max_length=2000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "project_type": "web",
                "message": "Hola, me gustaría hablar sobre un proyecto de desarrollo web."
            }
        }


class ContactResponseDTO(BaseModel):
    """DTO para respuesta de mensaje de contacto."""
    
    id: UUID
    name: str
    email: str
    project_type: str
    message: str
    status: str
    created_at: datetime
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContactListResponseDTO(BaseModel):
    """DTO para lista paginada de mensajes."""
    
    items: list[ContactResponseDTO]
    total: int
    skip: int = 0
    limit: int = 20


class ProjectTypeDTO(BaseModel):
    """DTO para tipo de proyecto."""
    
    value: str
    label: str
