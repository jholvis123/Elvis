"""
Interfaz del repositorio de Writeups.
Define el contrato que debe cumplir cualquier implementación.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.writeup import Writeup, WriteupStatus


class WriteupRepository(ABC):
    """Interfaz abstracta para el repositorio de writeups."""
    
    @abstractmethod
    def save(self, writeup: Writeup) -> Writeup:
        """Guarda un writeup (crear o actualizar)."""
        ...
    
    @abstractmethod
    def get_by_id(self, writeup_id: UUID) -> Optional[Writeup]:
        """Obtiene un writeup por su ID."""
        ...
    
    @abstractmethod
    def get_by_ctf_id(self, ctf_id: UUID) -> Optional[Writeup]:
        """Obtiene el writeup asociado a un CTF."""
        ...
    
    @abstractmethod
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WriteupStatus] = None,
    ) -> List[Writeup]:
        """Obtiene todos los writeups con paginación y filtros."""
        ...
    
    @abstractmethod
    def get_published(self, skip: int = 0, limit: int = 100) -> List[Writeup]:
        """Obtiene solo los writeups publicados."""
        ...
    
    @abstractmethod
    def get_by_author(self, author_id: UUID) -> List[Writeup]:
        """Obtiene writeups de un autor específico."""
        ...
    
    @abstractmethod
    def get_most_viewed(self, limit: int = 10) -> List[Writeup]:
        """Obtiene los writeups más vistos."""
        ...
    
    @abstractmethod
    def search(self, query: str) -> List[Writeup]:
        """Busca writeups por título o contenido."""
        ...
    
    @abstractmethod
    def delete(self, writeup_id: UUID) -> bool:
        """Elimina un writeup por su ID."""
        ...
    
    @abstractmethod
    def count(self, status: Optional[WriteupStatus] = None) -> int:
        """Cuenta el número de writeups."""
        ...
    
    @abstractmethod
    def increment_views(self, writeup_id: UUID) -> bool:
        """Incrementa el contador de vistas de un writeup."""
        ...
