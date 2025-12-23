"""
Entidad Writeup - Documentación de soluciones CTF.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum


class WriteupStatus(str, Enum):
    """Estados de un writeup."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Writeup:
    """Entidad de dominio para writeups de CTF."""
    
    title: str
    ctf_id: UUID
    content: str
    id: UUID = field(default_factory=uuid4)
    summary: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    status: WriteupStatus = WriteupStatus.DRAFT
    views: int = 0
    author_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    def publish(self) -> None:
        """Publica el writeup."""
        self.status = WriteupStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archiva el writeup."""
        self.status = WriteupStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def increment_views(self) -> None:
        """Incrementa el contador de vistas."""
        self.views += 1
    
    def add_tool(self, tool: str) -> None:
        """Añade una herramienta usada."""
        if tool not in self.tools_used:
            self.tools_used.append(tool)
            self.updated_at = datetime.utcnow()
    
    def add_technique(self, technique: str) -> None:
        """Añade una técnica utilizada."""
        if technique not in self.techniques:
            self.techniques.append(technique)
            self.updated_at = datetime.utcnow()
    
    def add_attachment(self, attachment_path: str) -> None:
        """Añade un archivo adjunto."""
        if attachment_path not in self.attachments:
            self.attachments.append(attachment_path)
            self.updated_at = datetime.utcnow()
    
    def update_content(self, content: str) -> None:
        """Actualiza el contenido del writeup."""
        self.content = content
        self.updated_at = datetime.utcnow()
    
    @property
    def is_published(self) -> bool:
        """Verifica si el writeup está publicado."""
        return self.status == WriteupStatus.PUBLISHED
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Writeup):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
