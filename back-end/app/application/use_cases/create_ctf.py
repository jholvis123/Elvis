"""
Caso de uso: Crear CTF.
"""

from typing import Optional
from uuid import UUID, uuid4

from ..dto.ctf_dto import CTFCreateDTO, CTFResponseDTO
from ...domain.entities.ctf import CTF, CTFLevel, CTFCategory, CTFStatus
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.services.ctf_service import CTFService


class CreateCTFUseCase:
    """Caso de uso para crear un nuevo CTF."""
    
    def __init__(
        self,
        ctf_repository: CTFRepository,
        ctf_service: CTFService,
    ):
        self.ctf_repository = ctf_repository
        self.ctf_service = ctf_service
    
    def execute(self, data: CTFCreateDTO) -> CTFResponseDTO:
        """
        Ejecuta el caso de uso de crear CTF.
        
        Args:
            data: DTO con los datos del CTF a crear.
            
        Returns:
            DTO con el CTF creado.
            
        Raises:
            ValueError: Si los datos son inválidos.
        """
        # Validar datos
        errors = self.ctf_service.validate_ctf_data(
            title=data.title,
            level=data.level,
            category=data.category,
        )
        
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        
        # Calcular puntos si no se especificaron
        points = data.points
        if points == 0:
            points = self.ctf_service.calculate_points(CTFLevel(data.level))
        
        # Crear entidad de dominio
        ctf_id = uuid4()
        
        # Procesar adjuntos
        attachments = []
        if data.attachments:
            from ...domain.entities.attachment import Attachment, AttachmentType
            from ...application.dto.ctf_dto import AttachmentDTO
            
            for att_dto in data.attachments:
                try:
                    att_id = UUID(att_dto.id) if att_dto.id else uuid4()
                except ValueError:
                    att_id = uuid4()
                
                attachment = Attachment(
                    id=att_id,
                    name=att_dto.name,
                    type=AttachmentType(att_dto.type),
                    url=att_dto.url,
                    size=att_dto.size,
                    mime_type=att_dto.mime_type,
                    ctf_id=ctf_id
                )
                attachments.append(attachment)
        
        ctf = CTF(
            id=ctf_id,
            title=data.title,
            level=CTFLevel(data.level),
            category=CTFCategory(data.category),
            platform=data.platform,
            description=data.description,
            points=points,
            machine_os=data.machine_os,
            skills=data.skills,
            hints=data.hints,
            author=data.author,
            is_active=data.is_active,
            status=CTFStatus.PUBLISHED if data.is_active else CTFStatus.DRAFT,
            attachments=attachments
        )
        
        # Establecer flag
        if data.flag:
            ctf.set_flag(data.flag.strip())
        
        # Persistir
        saved_ctf = self.ctf_repository.save(ctf)
        
        # Convertir a DTO de respuesta
        return self._to_response_dto(saved_ctf)
    
    def _to_response_dto(self, ctf: CTF) -> CTFResponseDTO:
        """Convierte una entidad CTF a DTO de respuesta."""
        # Convertir adjuntos a DTOs
        from ...application.dto.ctf_dto import AttachmentDTO
        
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
            has_writeup=False,
        )
