"""
Entidad Contact - Mensajes del formulario de contacto.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class ContactStatus(str, Enum):
    """Estados de un mensaje de contacto."""
    PENDING = "pending"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"


class ProjectType(str, Enum):
    """Tipos de proyecto para contacto."""
    WEB = "web"
    SECURITY = "security"
    CTF = "ctf"
    OTHER = "other"


@dataclass
class Contact:
    """Entidad de dominio para mensajes de contacto."""
    
    name: str
    email: str
    project_type: ProjectType
    message: str
    id: UUID = field(default_factory=uuid4)
    status: ContactStatus = ContactStatus.PENDING
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    
    def mark_as_read(self) -> None:
        """Marca el mensaje como leído."""
        self.status = ContactStatus.READ
        self.read_at = datetime.utcnow()
    
    def mark_as_replied(self) -> None:
        """Marca el mensaje como respondido."""
        self.status = ContactStatus.REPLIED
        self.replied_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archiva el mensaje."""
        self.status = ContactStatus.ARCHIVED
    
    @property
    def is_pending(self) -> bool:
        """Verifica si el mensaje está pendiente."""
        return self.status == ContactStatus.PENDING
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contact):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
