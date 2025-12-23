"""
DTOs para Attachments.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class AttachmentCreateDTO(BaseModel):
    """DTO para crear un adjunto."""
    
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    attachment_type: str = Field(..., description="file, url, docker")
    ctf_id: UUID
    url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "challenge.zip",
                "attachment_type": "url",
                "ctf_id": "123e4567-e89b-12d3-a456-426614174000",
                "url": "https://example.com/docker-image"
            }
        }


class AttachmentResponseDTO(BaseModel):
    """DTO para respuesta de adjunto."""
    
    id: UUID
    ctf_id: UUID
    filename: str
    attachment_type: str
    url: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AttachmentUploadResponseDTO(BaseModel):
    """DTO para respuesta de subida de archivo."""
    
    id: UUID
    filename: str
    attachment_type: str
    url: str
    size: int
    mime_type: str
    message: str = "Archivo subido exitosamente"


class AttachmentListResponseDTO(BaseModel):
    """DTO para lista de adjuntos."""
    
    items: List[AttachmentResponseDTO]
    total: int


class CategoryConfigDTO(BaseModel):
    """DTO para configuración de categoría."""
    
    category: str
    allowed_types: List[str]
    max_size: int
    max_files: int
    allowed_extensions: List[str]
