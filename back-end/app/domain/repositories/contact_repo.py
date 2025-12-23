"""
Repositorio abstracto para Contact.
Define la interfaz que debe implementar cualquier repositorio de contactos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.contact import Contact, ContactStatus


class ContactRepository(ABC):
    """Interfaz del repositorio de contactos."""
    
    @abstractmethod
    def save(self, contact: Contact) -> Contact:
        """Guarda un mensaje de contacto."""
        pass
    
    @abstractmethod
    def get_by_id(self, contact_id: UUID) -> Optional[Contact]:
        """Obtiene un mensaje por su ID."""
        pass
    
    @abstractmethod
    def get_all(
        self,
        status: Optional[ContactStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Contact]:
        """Obtiene todos los mensajes con filtros opcionales."""
        pass
    
    @abstractmethod
    def get_pending(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Obtiene mensajes pendientes."""
        pass
    
    @abstractmethod
    def delete(self, contact_id: UUID) -> bool:
        """Elimina un mensaje."""
        pass
    
    @abstractmethod
    def count(self, status: Optional[ContactStatus] = None) -> int:
        """Cuenta mensajes con filtro opcional de estado."""
        pass
