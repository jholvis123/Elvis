"""
DTOs para Writeups.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WriteupCreateDTO(BaseModel):
    """DTO para crear un writeup."""
    
    title: str = Field(..., min_length=3, max_length=200)
    ctf_id: Optional[UUID] = None
    content: str = Field(..., min_length=100, max_length=200000)
    summary: Optional[str] = Field(None, max_length=500)
    tools_used: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Lame Writeup - HackTheBox",
                "ctf_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "## Enumeration\n\nStarting with nmap...",
                "summary": "Exploitation of SMB vulnerability",
                "tools_used": ["nmap", "metasploit"],
                "techniques": ["smb enumeration", "exploit"]
            }
        }


class WriteupUpdateDTO(BaseModel):
    """DTO para actualizar un writeup."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=100, max_length=200000)
    summary: Optional[str] = Field(None, max_length=500)
    tools_used: Optional[List[str]] = None
    techniques: Optional[List[str]] = None


class TOCItemDTO(BaseModel):
    """DTO para ítem del índice de contenidos."""
    id: str
    text: str
    level: int


class WriteupResponseDTO(BaseModel):
    """DTO para respuesta de writeup."""
    
    id: UUID
    title: str
    ctf_id: Optional[UUID]
    content: str  # Markdown raw
    content_html: Optional[str] = None  # HTML renderizado
    summary: Optional[str]
    tools_used: List[str]
    techniques: List[str]
    attachments: List[str]
    status: str
    views: int
    author_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    read_time: int = 0  # Minutos estimados de lectura
    word_count: int = 0
    toc: List[TOCItemDTO] = Field(default_factory=list)
    languages_used: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class WriteupListResponseDTO(BaseModel):
    """DTO para lista paginada de writeups."""
    
    items: List[WriteupResponseDTO]
    total: int
    page: int
    size: int
    pages: int


class WriteupSummaryDTO(BaseModel):
    """DTO resumido de writeup (para listados)."""
    
    id: UUID
    title: str
    ctf_id: Optional[UUID]
    summary: Optional[str]
    status: str
    views: int
    created_at: datetime
    published_at: Optional[datetime]
    read_time: int = 0
    
    class Config:
        from_attributes = True
