"""
Interfaz del repositorio de usuarios.
Define el contrato que debe cumplir cualquier implementación.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user import User


class UserRepository(ABC):
    """Interfaz abstracta para el repositorio de usuarios."""
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Guarda un usuario (crear o actualizar)."""
        ...
    
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        ...
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email."""
        ...
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su username."""
        ...
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtiene todos los usuarios con paginación."""
        ...
    
    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Elimina un usuario por su ID."""
        ...
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Verifica si existe un usuario con el email dado."""
        ...
    
    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """Verifica si existe un usuario con el username dado."""
        ...
