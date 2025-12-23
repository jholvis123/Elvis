"""
Caso de uso: Crear CTF.
"""

from typing import Optional
from uuid import UUID

from ..dto.ctf_dto import CTFCreateDTO, CTFResponseDTO
from ...domain.entities.ctf import CTF, CTFLevel, CTFCategory
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
        ctf = CTF(
            title=data.title,
            level=CTFLevel(data.level),
            category=CTFCategory(data.category),
            platform=data.platform,
            description=data.description,
            points=points,
            machine_os=data.machine_os,
            tags=data.tags,
        )
        
        # Persistir
        saved_ctf = self.ctf_repository.save(ctf)
        
        # Convertir a DTO de respuesta
        return self._to_response_dto(saved_ctf)
    
    def _to_response_dto(self, ctf: CTF) -> CTFResponseDTO:
        """Convierte una entidad CTF a DTO de respuesta."""
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
            tags=ctf.tags,
            status=ctf.status.value,
            created_at=ctf.created_at,
            updated_at=ctf.updated_at,
            has_writeup=False,
        )
