"""
Entidad PortfolioProfile - Datos del perfil del portfolio.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class Highlight:
    """Estadística destacada del portfolio."""
    label: str
    value: str
    icon: Optional[str] = None
    order: int = 0


@dataclass
class PortfolioProfile:
    """Entidad de dominio para el perfil del portfolio."""
    
    name: str
    title: str
    id: UUID = field(default_factory=uuid4)
    bio: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    stack_items: List[str] = field(default_factory=list)
    about_points: List[str] = field(default_factory=list)
    highlights: List[Highlight] = field(default_factory=list)
    social_links: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def add_role(self, role: str) -> None:
        """Añade un rol."""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.utcnow()
    
    def add_stack_item(self, item: str) -> None:
        """Añade un item al stack."""
        if item not in self.stack_items:
            self.stack_items.append(item)
            self.updated_at = datetime.utcnow()
    
    def add_highlight(self, label: str, value: str, icon: Optional[str] = None) -> None:
        """Añade un highlight."""
        self.highlights.append(Highlight(label=label, value=value, icon=icon, order=len(self.highlights)))
        self.updated_at = datetime.utcnow()
    
    def set_social_link(self, platform: str, url: str) -> None:
        """Establece un enlace social."""
        self.social_links[platform] = url
        self.updated_at = datetime.utcnow()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortfolioProfile):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
