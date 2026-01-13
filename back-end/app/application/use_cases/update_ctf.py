"""
Caso de uso: Actualizar CTF.
"""

from typing import Optional
from uuid import UUID

from ..dto.ctf_dto import CTFUpdateDTO, CTFResponseDTO
from ...domain.entities.ctf import CTFLevel, CTFCategory
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.services.ctf_service import CTFService


class UpdateCTFUseCase:
    """Caso de uso para actualizar un CTF existente."""
    
    def __init__(
        self,
        ctf_repository: CTFRepository,
        writeup_repository: WriteupRepository,
        ctf_service: CTFService,
    ):
        self.ctf_repository = ctf_repository
        self.writeup_repository = writeup_repository
        self.ctf_service = ctf_service
    
    def execute(self, ctf_id: UUID, data: CTFUpdateDTO, user_id: Optional[UUID] = None) -> Optional[CTFResponseDTO]:
        """
        Ejecuta el caso de uso de actualizar un CTF.
        
        Args:
            ctf_id: ID del CTF a actualizar.
            data: DTO con los datos a actualizar.
            user_id: ID del usuario actualizador.
            
        Returns:
            DTO del CTF actualizado o None si no existe.
            
        Raises:
            ValueError: Si los datos son inválidos.
        """
        # Obtener CTF existente
        ctf = self.ctf_repository.get_by_id(ctf_id)
        if not ctf:
            return None
        
        # Actualizar campos si se proporcionan
        if data.title is not None:
            ctf.title = data.title
        
        if data.level is not None:
            ctf.level = CTFLevel(data.level)
        
        if data.category is not None:
            ctf.category = CTFCategory(data.category)
        
        if data.platform is not None:
            ctf.platform = data.platform
        
        if data.description is not None:
            ctf.description = data.description
        
        if data.points is not None:
            ctf.points = data.points
        
        if data.machine_os is not None:
            ctf.machine_os = data.machine_os
        
        if data.skills is not None:
            ctf.skills = data.skills

        if data.hints is not None:
            ctf.hints = data.hints

        if data.flag is not None:
             is_regex = data.is_flag_regex if data.is_flag_regex is not None else ctf.is_flag_regex
             ctf.set_flag(data.flag.strip(), is_regex=is_regex)
        
        if data.solved is not None and data.solved and not ctf.solved:
            ctf.mark_as_solved()
        
        if data.is_active is not None:
            ctf.is_active = data.is_active
        
        # Auditoría
        if user_id:
            ctf.updated_by_id = user_id
            
        # Persistir cambios
        saved_ctf = self.ctf_repository.save(ctf)
        
        # Verificar si tiene writeup
        writeup = self.writeup_repository.get_by_ctf_id(ctf_id)
        
        return CTFResponseDTO(
            id=saved_ctf.id,
            title=saved_ctf.title,
            level=saved_ctf.level.value,
            category=saved_ctf.category.value,
            platform=saved_ctf.platform,
            description=saved_ctf.description,
            points=saved_ctf.points,
            solved=saved_ctf.solved,
            solved_at=saved_ctf.solved_at,
            machine_os=saved_ctf.machine_os,
            skills=saved_ctf.skills,
            hints=saved_ctf.hints,
            author=saved_ctf.author,
            solved_count=saved_ctf.solved_count,
            is_active=saved_ctf.is_active,
            status=saved_ctf.status.value,
            created_at=saved_ctf.created_at,
            updated_at=saved_ctf.updated_at,
            has_writeup=writeup is not None,
        )
    
    def publish(self, ctf_id: UUID) -> Optional[CTFResponseDTO]:
        """
        Publica un CTF.
        
        Args:
            ctf_id: ID del CTF a publicar.
            
        Returns:
            DTO del CTF publicado o None si no existe.
            
        Raises:
            ValueError: Si no puede ser publicado.
        """
        ctf = self.ctf_repository.get_by_id(ctf_id)
        if not ctf:
            return None
        
        can_publish, error = self.ctf_service.can_publish(ctf)
        if not can_publish:
            raise ValueError(error)
        
        ctf.publish()
        saved_ctf = self.ctf_repository.save(ctf)
        
        writeup = self.writeup_repository.get_by_ctf_id(ctf_id)
        
        return CTFResponseDTO(
            id=saved_ctf.id,
            title=saved_ctf.title,
            level=saved_ctf.level.value,
            category=saved_ctf.category.value,
            platform=saved_ctf.platform,
            description=saved_ctf.description,
            points=saved_ctf.points,
            solved=saved_ctf.solved,
            solved_at=saved_ctf.solved_at,
            machine_os=saved_ctf.machine_os,
            skills=saved_ctf.skills,
            hints=saved_ctf.hints,
            author=saved_ctf.author,
            solved_count=saved_ctf.solved_count,
            is_active=saved_ctf.is_active,
            status=saved_ctf.status.value,
            created_at=saved_ctf.created_at,
            updated_at=saved_ctf.updated_at,
            has_writeup=writeup is not None,
        )
