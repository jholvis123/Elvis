"""
Interfaz del repositorio de proyectos.
Define el contrato que debe cumplir cualquier implementación.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.project import Project, ProjectStatus


class ProjectRepository(ABC):
    """Interfaz abstracta para el repositorio de proyectos."""
    
    @abstractmethod
    def save(self, project: Project) -> Project:
        """Guarda un proyecto (crear o actualizar)."""
        ...
    
    @abstractmethod
    def get_by_id(self, project_id: UUID) -> Optional[Project]:
        """Obtiene un proyecto por su ID."""
        ...
    
    @abstractmethod
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProjectStatus] = None,
    ) -> List[Project]:
        """Obtiene todos los proyectos con paginación y filtros."""
        ...
    
    @abstractmethod
    def get_featured(self, limit: int = 5) -> List[Project]:
        """Obtiene los proyectos destacados."""
        ...
    
    @abstractmethod
    def get_published(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Obtiene solo los proyectos publicados."""
        ...
    
    @abstractmethod
    def get_by_technology(self, technology: str) -> List[Project]:
        """Obtiene proyectos que usen una tecnología específica."""
        ...
    
    @abstractmethod
    def delete(self, project_id: UUID) -> bool:
        """Elimina un proyecto por su ID."""
        ...
    
    @abstractmethod
    def count(self, status: Optional[ProjectStatus] = None) -> int:
        """Cuenta el número de proyectos."""
        ...
