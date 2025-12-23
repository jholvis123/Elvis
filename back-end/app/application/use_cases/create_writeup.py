"""
Caso de uso: Crear Writeup.
"""

from typing import Optional
from uuid import UUID

from ..dto.writeup_dto import WriteupCreateDTO, WriteupResponseDTO
from ...domain.entities.writeup import Writeup
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.services.writeup_service import WriteupService


class CreateWriteupUseCase:
    """Caso de uso para crear un nuevo writeup."""
    
    def __init__(
        self,
        writeup_repository: WriteupRepository,
        writeup_service: WriteupService,
    ):
        self.writeup_repository = writeup_repository
        self.writeup_service = writeup_service
    
    def execute(
        self,
        data: WriteupCreateDTO,
        author_id: Optional[UUID] = None,
    ) -> WriteupResponseDTO:
        """
        Ejecuta el caso de uso de crear un writeup.
        
        Args:
            data: DTO con los datos del writeup.
            author_id: ID del autor (opcional).
            
        Returns:
            DTO del writeup creado.
            
        Raises:
            ValueError: Si los datos son inválidos o ya existe un writeup.
        """
        # Validar que se puede crear
        can_create, error = self.writeup_service.can_create_writeup(data.ctf_id)
        if not can_create:
            raise ValueError(error)
        
        # Validar contenido
        errors = self.writeup_service.validate_writeup_content(data.content)
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        
        # Extraer herramientas del contenido si no se especificaron
        tools = data.tools_used
        if not tools:
            tools = self.writeup_service.extract_tools_from_content(data.content)
        
        # Crear entidad
        writeup = Writeup(
            title=data.title,
            ctf_id=data.ctf_id,
            content=data.content,
            summary=data.summary,
            tools_used=tools,
            techniques=data.techniques,
            author_id=author_id,
        )
        
        # Persistir
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
