"""
Entidad User - Usuario del sistema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    """Entidad de dominio para usuarios."""
    
    email: str
    username: str
    hashed_password: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def activate(self) -> None:
        """Activa el usuario."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Desactiva el usuario."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def promote_to_admin(self) -> None:
        """Promueve al usuario a administrador."""
        self.is_admin = True
        self.updated_at = datetime.utcnow()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
