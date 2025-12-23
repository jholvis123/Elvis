"""
Interfaz del repositorio de CTFs.
Define el contrato que debe cumplir cualquier implementación.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.ctf import CTF, CTFLevel, CTFCategory, CTFStatus


class CTFRepository(ABC):
    """Interfaz abstracta para el repositorio de CTFs."""
    
    @abstractmethod
    def save(self, ctf: CTF) -> CTF:
        """Guarda un CTF (crear o actualizar)."""
        ...
    
    @abstractmethod
    def get_by_id(self, ctf_id: UUID) -> Optional[CTF]:
        """Obtiene un CTF por su ID."""
        ...
    
    @abstractmethod
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CTFStatus] = None,
    ) -> List[CTF]:
        """Obtiene todos los CTFs con paginación y filtros."""
        ...
    
    @abstractmethod
    def get_by_level(self, level: CTFLevel) -> List[CTF]:
        """Obtiene CTFs por nivel de dificultad."""
        ...
    
    @abstractmethod
    def get_by_category(self, category: CTFCategory) -> List[CTF]:
        """Obtiene CTFs por categoría."""
        ...
    
    @abstractmethod
    def get_by_platform(self, platform: str) -> List[CTF]:
        """Obtiene CTFs por plataforma."""
        ...
    
    @abstractmethod
    def get_published(self, skip: int = 0, limit: int = 100) -> List[CTF]:
        """Obtiene solo los CTFs publicados."""
        ...
    
    @abstractmethod
    def get_solved(self) -> List[CTF]:
        """Obtiene los CTFs resueltos."""
        ...
    
    @abstractmethod
    def search(self, query: str) -> List[CTF]:
        """Busca CTFs por título o tags."""
        ...
    
    @abstractmethod
    def delete(self, ctf_id: UUID) -> bool:
        """Elimina un CTF por su ID."""
        ...
    
    @abstractmethod
    def count(
        self,
        status: Optional[CTFStatus] = None,
        category: Optional[CTFCategory] = None,
    ) -> int:
        """Cuenta el número de CTFs con filtros opcionales."""
        ...
    
    @abstractmethod
    def get_statistics(self) -> dict:
        """Obtiene estadísticas de CTFs (por nivel, categoría, etc.)."""
        ...
