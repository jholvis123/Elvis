"""
Caso de uso: Publicar Writeup.
"""

from typing import Optional
from uuid import UUID

from ..dto.writeup_dto import WriteupResponseDTO
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.services.writeup_service import WriteupService


class PublishWriteupUseCase:
    """Caso de uso para publicar un writeup."""
    
    def __init__(
        self,
        writeup_repository: WriteupRepository,
        writeup_service: WriteupService,
    ):
        self.writeup_repository = writeup_repository
        self.writeup_service = writeup_service
    
    def execute(self, writeup_id: UUID) -> Optional[WriteupResponseDTO]:
        """
        Ejecuta el caso de uso de publicar un writeup.
        
        Args:
            writeup_id: ID del writeup a publicar.
            
        Returns:
            DTO del writeup publicado o None si no existe.
            
        Raises:
            ValueError: Si no puede ser publicado.
        """
        # Obtener writeup
        writeup = self.writeup_repository.get_by_id(writeup_id)
        if not writeup:
            return None
        
        # Validar que puede ser publicado
        can_publish, error = self.writeup_service.can_publish(writeup)
        if not can_publish:
            raise ValueError(error)
        
        # Publicar
        writeup.publish()
        saved_writeup = self.writeup_repository.save(writeup)
        
        # Calcular tiempo de lectura
        read_time = self.writeup_service.calculate_read_time(saved_writeup.content)
        
        return WriteupResponseDTO(
            id=saved_writeup.id,
            title=saved_writeup.title,
            ctf_id=saved_writeup.ctf_id,
            content=saved_writeup.content,
            summary=saved_writeup.summary,
            tools_used=saved_writeup.tools_used,
            techniques=saved_writeup.techniques,
            attachments=saved_writeup.attachments,
            status=saved_writeup.status.value,
            views=saved_writeup.views,
            author_id=saved_writeup.author_id,
            created_at=saved_writeup.created_at,
            updated_at=saved_writeup.updated_at,
            published_at=saved_writeup.published_at,
            read_time=read_time,
        )
