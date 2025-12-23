"""
Repositorio abstracto para Attachments.
Define la interfaz que debe implementar cualquier repositorio de adjuntos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.attachment import Attachment


class AttachmentRepository(ABC):
    """Interfaz del repositorio de adjuntos."""
    
    @abstractmethod
    def save(self, attachment: Attachment) -> Attachment:
        """Guarda un adjunto."""
        pass
    
    @abstractmethod
    def get_by_id(self, attachment_id: UUID) -> Optional[Attachment]:
        """Obtiene un adjunto por su ID."""
        pass
    
    @abstractmethod
    def get_by_ctf_id(self, ctf_id: UUID) -> List[Attachment]:
        """Obtiene todos los adjuntos de un CTF."""
        pass
    
    @abstractmethod
    def delete(self, attachment_id: UUID) -> bool:
        """Elimina un adjunto."""
        pass
    
    @abstractmethod
    def delete_by_ctf_id(self, ctf_id: UUID) -> int:
        """Elimina todos los adjuntos de un CTF. Retorna cantidad eliminada."""
        pass
