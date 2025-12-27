"""
Caso de uso: Obtener CTF por ID.
"""

from typing import Optional
from uuid import UUID

from ..dto.ctf_dto import CTFResponseDTO
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.writeup_repo import WriteupRepository


class GetCTFUseCase:
    """Caso de uso para obtener un CTF por su ID."""
    
    def __init__(
        self,
        ctf_repository: CTFRepository,
        writeup_repository: WriteupRepository,
    ):
        self.ctf_repository = ctf_repository
        self.writeup_repository = writeup_repository
    
    def execute(self, ctf_id: UUID) -> Optional[CTFResponseDTO]:
        """
        Ejecuta el caso de uso de obtener un CTF.
        
        Args:
            ctf_id: ID del CTF a obtener.
            
        Returns:
            DTO del CTF o None si no existe.
        """
        ctf = self.ctf_repository.get_by_id(ctf_id)
        
        if not ctf:
            return None
        
        # Verificar si tiene writeup
        writeup = self.writeup_repository.get_by_ctf_id(ctf_id)
        
        # Convertir adjuntos a DTOs
        from ..dto.ctf_dto import AttachmentDTO
        
        attachment_dtos = [
            AttachmentDTO(
                id=str(a.id),
                name=a.name,
                type=a.type.value,
                url=a.url,
                size=a.size,
                mime_type=a.mime_type
            )
            for a in ctf.attachments
        ] if ctf.attachments else []

        return CTFResponseDTO(
            id=ctf.id,
            title=ctf.title,
            level=ctf.level.value,
            category=ctf.category.value,
            platform=ctf.platform,
            description=ctf.description,
            points=ctf.points,
            solved=ctf.solved,
            solved_at=ctf.solved_at,
            machine_os=ctf.machine_os,
            skills=ctf.skills,
            hints=ctf.hints,
            author=ctf.author,
            solved_count=ctf.solved_count,
            is_active=ctf.is_active,
            attachments=attachment_dtos,
            status=ctf.status.value,
            created_at=ctf.created_at,
            updated_at=ctf.updated_at,
            has_writeup=writeup is not None,
        )
