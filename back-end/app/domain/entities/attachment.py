"""
Entidad Attachment - Archivos adjuntos para CTFs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class AttachmentType(str, Enum):
    """Tipos de adjuntos."""
    FILE = "file"
    URL = "url"
    DOCKER = "docker"


@dataclass
class Attachment:
    """Entidad de dominio para archivos adjuntos."""
    
    name: str
    type: AttachmentType
    id: UUID = field(default_factory=uuid4)
    ctf_id: Optional[UUID] = None
    url: Optional[str] = None           # URL del recurso o path del archivo
    file_path: Optional[str] = None     # Path local del archivo
    size: Optional[int] = None          # Tamaño en bytes
    mime_type: Optional[str] = None     # MIME type del archivo
    checksum: Optional[str] = None      # Hash MD5/SHA256 del archivo
    created_at: datetime = field(default_factory=datetime.utcnow)
    uploaded_by: Optional[UUID] = None  # ID del usuario que subió
    
    @property
    def is_file(self) -> bool:
        """Verifica si es un archivo."""
        return self.type == AttachmentType.FILE
    
    @property
    def is_url(self) -> bool:
        """Verifica si es una URL."""
        return self.type == AttachmentType.URL
    
    @property
    def is_docker(self) -> bool:
        """Verifica si es un contenedor Docker."""
        return self.type == AttachmentType.DOCKER
    
    @property
    def size_formatted(self) -> str:
        """Retorna el tamaño formateado."""
        if not self.size:
            return ""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización."""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type.value,
            "url": self.url,
            "size": self.size,
            "mime_type": self.mime_type,
        }
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Attachment):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
