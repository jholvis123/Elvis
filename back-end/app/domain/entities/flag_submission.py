"""
Entidad FlagSubmission - Registro de intentos de flags.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class FlagSubmission:
    """Entidad de dominio para registrar intentos de flags."""
    
    ctf_id: UUID
    flag: str
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    is_correct: bool = False
    ip_address: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FlagSubmission):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
