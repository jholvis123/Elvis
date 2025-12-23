"""
Router de CTFs.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from ...application.dto.ctf_dto import (
    CTFCreateDTO,
    CTFUpdateDTO,
    CTFResponseDTO,
    CTFListResponseDTO,
    CTFStatisticsDTO,
)
from ...application.dto.flag_dto import (
    FlagSubmitDTO,
    FlagSubmitResponseDTO,
)
from ...application.use_cases import (
    CreateCTFUseCase,
    ListCTFsUseCase,
    GetCTFUseCase,
    UpdateCTFUseCase,
    DeleteCTFUseCase,
)
from ...domain.entities.user import User
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.services.ctf_service import CTFService
from ...domain.services.flag_service import FlagService
from ..dependencies import (
    get_ctf_repository,
    get_writeup_repository,
    get_ctf_service,
    get_flag_service,
    get_current_user,
    get_current_admin,
    get_current_user_optional,
)

router = APIRouter(prefix="/ctfs", tags=["CTFs"])


@router.get("", response_model=CTFListResponseDTO)
async def list_ctfs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    level: Optional[str] = None,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Lista CTFs con filtros y paginación."""
    use_case = ListCTFsUseCase(ctf_repo, writeup_repo)
    
    return use_case.execute(
        page=page,
        size=size,
        level=level,
        category=category,
        platform=platform,
        search=search,
    )


@router.get("/statistics", response_model=CTFStatisticsDTO)
async def get_statistics(
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Obtiene estadísticas de CTFs."""
    use_case = ListCTFsUseCase(ctf_repo, writeup_repo)
    return use_case.get_statistics()


@router.get("/{ctf_id}", response_model=CTFResponseDTO)
async def get_ctf(
    ctf_id: UUID,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Obtiene un CTF por su ID."""
    use_case = GetCTFUseCase(ctf_repo, writeup_repo)
    result = use_case.execute(ctf_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CTF not found",
        )
    
    return result


@router.post("", response_model=CTFResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_ctf(
    data: CTFCreateDTO,
    current_user: User = Depends(get_current_user),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    ctf_service: CTFService = Depends(get_ctf_service),
):
    """Crea un nuevo CTF (requiere autenticación)."""
    use_case = CreateCTFUseCase(ctf_repo, ctf_service)
    
    try:
        return use_case.execute(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{ctf_id}", response_model=CTFResponseDTO)
async def update_ctf(
    ctf_id: UUID,
    data: CTFUpdateDTO,
    current_user: User = Depends(get_current_user),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    ctf_service: CTFService = Depends(get_ctf_service),
):
    """Actualiza un CTF existente (requiere autenticación)."""
    use_case = UpdateCTFUseCase(ctf_repo, writeup_repo, ctf_service)
    
    result = use_case.execute(ctf_id, data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CTF not found",
        )
    
    return result


@router.post("/{ctf_id}/publish", response_model=CTFResponseDTO)
async def publish_ctf(
    ctf_id: UUID,
    current_user: User = Depends(get_current_user),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    ctf_service: CTFService = Depends(get_ctf_service),
):
    """Publica un CTF (requiere autenticación)."""
    use_case = UpdateCTFUseCase(ctf_repo, writeup_repo, ctf_service)
    
    try:
        result = use_case.publish(ctf_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CTF not found",
            )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{ctf_id}/submit", response_model=FlagSubmitResponseDTO)
async def submit_flag(
    ctf_id: UUID,
    data: FlagSubmitDTO,
    request: Request,
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    flag_service: FlagService = Depends(get_flag_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Envía una flag para validación.
    
    - **flag**: La flag a verificar (formato: FLAG{...} o similar)
    
    Retorna si la flag es correcta y el mensaje correspondiente.
    Funciona con o sin autenticación (usuario opcional).
    """
    # Obtener el CTF
    ctf = ctf_repo.get_by_id(ctf_id)
    if not ctf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CTF not found",
        )
    
    # Verificar si el CTF está activo
    if not ctf.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This challenge is not active",
        )
    
    # Obtener IP del cliente
    ip_address = request.client.host if request.client else None
    user_id = current_user.id if current_user else None
    
    # Intentar enviar la flag
    try:
        result = flag_service.submit_flag(
            ctf_id=ctf_id,
            submitted_flag=data.flag,
            user_id=user_id,
            ip_address=ip_address,
        )
        
        # Si es correcta, actualizar el contador del CTF
        if result["is_correct"]:
            ctf.increment_solved_count()
            ctf_repo.save(ctf)
        
        return FlagSubmitResponseDTO(
            is_correct=result["is_correct"],
            message=result["message"],
            attempts_remaining=result.get("attempts_remaining"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{ctf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ctf(
    ctf_id: UUID,
    force: bool = False,
    current_user: User = Depends(get_current_admin),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Elimina un CTF (requiere admin)."""
    use_case = DeleteCTFUseCase(ctf_repo, writeup_repo)
    
    try:
        deleted = use_case.execute(ctf_id, force=force)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CTF not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
