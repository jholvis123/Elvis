"""
Entidad Project - Proyectos del portafolio.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum


class ProjectStatus(str, Enum):
    """Estados posibles de un proyecto."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Project:
    """Entidad de dominio para proyectos del portafolio."""
    
    title: str
    description: str
    id: UUID = field(default_factory=uuid4)
    short_description: Optional[str] = None
    image_url: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.DRAFT
    featured: bool = False
    order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def publish(self) -> None:
        """Publica el proyecto."""
        self.status = ProjectStatus.PUBLISHED
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archiva el proyecto."""
        self.status = ProjectStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def set_featured(self, featured: bool) -> None:
        """Marca o desmarca como destacado."""
        self.featured = featured
        self.updated_at = datetime.utcnow()
    
    def add_technology(self, technology: str) -> None:
        """Añade una tecnología al proyecto."""
        if technology not in self.technologies:
            self.technologies.append(technology)
            self.updated_at = datetime.utcnow()
    
    def add_highlight(self, highlight: str) -> None:
        """Añade un highlight al proyecto."""
        if highlight not in self.highlights:
            self.highlights.append(highlight)
            self.updated_at = datetime.utcnow()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Project):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
