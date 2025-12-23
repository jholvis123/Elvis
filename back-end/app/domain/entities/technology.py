"""
Entidad Technology - Tecnologías/skills del portafolio.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class TechnologyCategory(str, Enum):
    """Categorías de tecnologías."""
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    DEVOPS = "devops"
    SECURITY = "security"
    TOOL = "tool"
    OTHER = "other"


@dataclass
class Technology:
    """Entidad de dominio para tecnologías y habilidades."""
    
    name: str
    category: TechnologyCategory
    id: UUID = field(default_factory=uuid4)
    icon: Optional[str] = None
    proficiency: int = 0  # 0-100
    years_experience: float = 0.0
    is_featured: bool = False
    order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def set_proficiency(self, level: int) -> None:
        """Establece el nivel de competencia (0-100)."""
        if 0 <= level <= 100:
            self.proficiency = level
            self.updated_at = datetime.utcnow()
        else:
            raise ValueError("Proficiency must be between 0 and 100")
    
    def set_featured(self, featured: bool) -> None:
        """Marca o desmarca como destacada."""
        self.is_featured = featured
        self.updated_at = datetime.utcnow()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Technology):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
