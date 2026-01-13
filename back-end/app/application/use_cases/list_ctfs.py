"""
Caso de uso: Listar CTFs.
"""

from typing import List, Optional
from math import ceil

from ..dto.ctf_dto import CTFResponseDTO, CTFListResponseDTO, CTFStatisticsDTO
from ...domain.entities.ctf import CTFLevel, CTFCategory, CTFStatus
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.writeup_repo import WriteupRepository


class ListCTFsUseCase:
    """Caso de uso para listar CTFs con filtros y paginación."""
    
    def __init__(
        self,
        ctf_repository: CTFRepository,
        writeup_repository: WriteupRepository,
    ):
        self.ctf_repository = ctf_repository
        self.writeup_repository = writeup_repository
    
    def execute(
        self,
        page: int = 1,
        size: int = 10,
        level: Optional[str] = None,
        category: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> CTFListResponseDTO:
        """
        Ejecuta el caso de uso de listar CTFs.
        
        Args:
            page: Número de página (1-indexed).
            size: Tamaño de página.
            level: Filtro por nivel.
            category: Filtro por categoría.
            platform: Filtro por plataforma.
            status: Filtro por estado.
            search: Término de búsqueda.
            
        Returns:
            Lista paginada de CTFs.
        """
        skip = (page - 1) * size
        
        # Obtener CTFs según filtros
        if search:
            ctfs = self.ctf_repository.search(search)
        elif status:
            ctf_status = CTFStatus(status)
            ctfs = self.ctf_repository.get_all(skip=skip, limit=size, status=ctf_status)
        else:
            ctfs = self.ctf_repository.get_published(skip=skip, limit=size)
        
        # Aplicar filtros adicionales en memoria (se podría optimizar en el repo)
        if level:
            ctf_level = CTFLevel(level)
            ctfs = [c for c in ctfs if c.level == ctf_level]
        
        if category:
            ctf_category = CTFCategory(category)
            ctfs = [c for c in ctfs if c.category == ctf_category]
        
        if platform:
            ctfs = [c for c in ctfs if c.platform.lower() == platform.lower()]
        
        # Contar total
        total = self.ctf_repository.count(
            status=CTFStatus(status) if status else CTFStatus.PUBLISHED
        )
        
        # Convertir a DTOs
        items = [self._to_response_dto(ctf) for ctf in ctfs]
        
        return CTFListResponseDTO(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=ceil(total / size) if size > 0 else 0,
        )
    
    def execute_admin(
        self,
        page: int = 1,
        size: int = 10,
        level: Optional[str] = None,
        category: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> CTFListResponseDTO:
        """
        Lista TODOS los CTFs para administradores (incluye drafts).
        
        Args:
            page: Número de página (1-indexed).
            size: Tamaño de página.
            level: Filtro por nivel.
            category: Filtro por categoría.
            platform: Filtro por plataforma.
            status: Filtro por estado (draft, published, archived).
            search: Término de búsqueda.
            
        Returns:
            Lista paginada de CTFs.
        """
        skip = (page - 1) * size
        
        # Obtener todos los CTFs (sin filtro de estado por defecto)
        if search:
            ctfs = self.ctf_repository.search(search)
        else:
            ctf_status = CTFStatus(status) if status else None
            ctfs = self.ctf_repository.get_all(skip=skip, limit=size, status=ctf_status)
        
        # Aplicar filtros adicionales
        if level:
            ctf_level = CTFLevel(level)
            ctfs = [c for c in ctfs if c.level == ctf_level]
        
        if category:
            ctf_category = CTFCategory(category)
            ctfs = [c for c in ctfs if c.category == ctf_category]
        
        if platform:
            ctfs = [c for c in ctfs if c.platform.lower() == platform.lower()]
        
        # Contar total (sin filtro de estado para admin)
        total = self.ctf_repository.count(
            status=CTFStatus(status) if status else None
        )
        
        # Convertir a DTOs
        items = [self._to_response_dto(ctf) for ctf in ctfs]
        
        return CTFListResponseDTO(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=ceil(total / size) if size > 0 else 0,
        )
    
        solved_ctfs = self.ctf_repository.get_solved()
        
        return CTFStatisticsDTO(
            total=total,
            solved=len(solved_ctfs),
            total_points=stats.get("total_points", 0),
            earned_points=stats.get("earned_points", 0),
            by_level=stats.get("by_level", {}),
            by_category=stats.get("by_category", {}),
            by_platform=stats.get("by_platform", {}),
        )
    
    def _to_response_dto(self, ctf) -> CTFResponseDTO:
        """Convierte una entidad CTF a DTO de respuesta."""
        # Verificar si tiene writeup
        writeup = self.writeup_repository.get_by_ctf_id(ctf.id)
        
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
            status=ctf.status.value,
            created_at=ctf.created_at,
            updated_at=ctf.updated_at,
            has_writeup=writeup is not None,
        )
