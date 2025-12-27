"""
Router de Writeups.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...application.dto.writeup_dto import (
    WriteupCreateDTO,
    WriteupUpdateDTO,
    WriteupResponseDTO,
    WriteupListResponseDTO,
    WriteupSummaryDTO,
)
from ...application.use_cases import (
    CreateWriteupUseCase,
    PublishWriteupUseCase,
)
from ...domain.entities.user import User
from ...domain.entities.writeup import Writeup, WriteupStatus
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.services.writeup_service import WriteupService
from ..dependencies import (
    get_writeup_repository,
    get_ctf_repository,
    get_writeup_service,
    get_current_user,
    get_current_admin,
)

router = APIRouter(prefix="/writeups", tags=["Writeups"])


@router.get("", response_model=WriteupListResponseDTO)
async def list_writeups(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    writeup_service: WriteupService = Depends(get_writeup_service),
):
    """Lista writeups con filtros y paginación."""
    skip = (page - 1) * size
    
    if search:
        writeups = writeup_repo.search(search)
    else:
        writeups = writeup_repo.get_published(skip=skip, limit=size)
    
    total = writeup_repo.count(status=WriteupStatus.PUBLISHED)
    
    items = [
        WriteupResponseDTO(
            id=w.id,
            title=w.title,
            ctf_id=w.ctf_id,
            content=w.content,
            summary=w.summary,
            tools_used=w.tools_used,
            techniques=w.techniques,
            attachments=w.attachments,
            status=w.status.value,
            views=w.views,
            author_id=w.author_id,
            created_at=w.created_at,
            updated_at=w.updated_at,
            published_at=w.published_at,
            read_time=writeup_service.calculate_read_time(w.content),
        )
        for w in writeups
    ]
    
    from math import ceil
    return WriteupListResponseDTO(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size > 0 else 0,
    )


@router.get("/popular", response_model=List[WriteupSummaryDTO])
async def get_popular_writeups(
    limit: int = Query(10, ge=1, le=100),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Obtiene los writeups más vistos."""
    writeups = writeup_repo.get_most_viewed(limit=limit)
    
    return [
        WriteupSummaryDTO(
            id=w.id,
            title=w.title,
            ctf_id=w.ctf_id,
            summary=w.summary,
            status=w.status.value,
            views=w.views,
            created_at=w.created_at,
            published_at=w.published_at,
        )
        for w in writeups
    ]


@router.get("/ctf/{ctf_id}", response_model=WriteupResponseDTO)
async def get_writeup_by_ctf(
    ctf_id: UUID,
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    writeup_service: WriteupService = Depends(get_writeup_service),
):
    """Obtiene el writeup asociado a un CTF."""
    writeup = writeup_repo.get_by_ctf_id(ctf_id)
    
    if not writeup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writeup not found for this CTF",
        )
    
    # Incrementar vistas
    writeup_repo.increment_views(writeup.id)
    
    return WriteupResponseDTO(
        id=writeup.id,
        title=writeup.title,
        ctf_id=writeup.ctf_id,
        content=writeup.content,
        summary=writeup.summary,
        tools_used=writeup.tools_used,
        techniques=writeup.techniques,
        attachments=writeup.attachments,
        status=writeup.status.value,
        views=writeup.views + 1,
        author_id=writeup.author_id,
        created_at=writeup.created_at,
        updated_at=writeup.updated_at,
        published_at=writeup.published_at,
        read_time=writeup_service.calculate_read_time(writeup.content),
    )


@router.get("/{writeup_id}", response_model=WriteupResponseDTO)
async def get_writeup(
    writeup_id: UUID,
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    writeup_service: WriteupService = Depends(get_writeup_service),
):
    """Obtiene un writeup por su ID."""
    writeup = writeup_repo.get_by_id(writeup_id)
    
    if not writeup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writeup not found",
        )
    
    # Incrementar vistas
    writeup_repo.increment_views(writeup_id)
    
    return WriteupResponseDTO(
        id=writeup.id,
        title=writeup.title,
        ctf_id=writeup.ctf_id,
        content=writeup.content,
        summary=writeup.summary,
        tools_used=writeup.tools_used,
        techniques=writeup.techniques,
        attachments=writeup.attachments,
        status=writeup.status.value,
        views=writeup.views + 1,
        author_id=writeup.author_id,
        created_at=writeup.created_at,
        updated_at=writeup.updated_at,
        published_at=writeup.published_at,
        read_time=writeup_service.calculate_read_time(writeup.content),
    )


@router.post("", response_model=WriteupResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_writeup(
    data: WriteupCreateDTO,
    current_user: User = Depends(get_current_admin),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    writeup_service: WriteupService = Depends(get_writeup_service),
):
    """Crea un nuevo writeup (requiere autenticación)."""
    use_case = CreateWriteupUseCase(writeup_repo, writeup_service)
    
    try:
        return use_case.execute(data, author_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{writeup_id}", response_model=WriteupResponseDTO)
async def update_writeup(
    writeup_id: UUID,
    data: WriteupUpdateDTO,
    current_user: User = Depends(get_current_admin),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    writeup_service: WriteupService = Depends(get_writeup_service),
):
    """Actualiza un writeup existente (requiere autenticación)."""
    writeup = writeup_repo.get_by_id(writeup_id)
    
    if not writeup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writeup not found",
        )
    
    # Actualizar campos
    if data.title is not None:
        writeup.title = data.title
    if data.content is not None:
        writeup.update_content(data.content)
    if data.summary is not None:
        writeup.summary = data.summary
    if data.tools_used is not None:
        writeup.tools_used = data.tools_used
    if data.techniques is not None:
        writeup.techniques = data.techniques
    
    saved_writeup = writeup_repo.save(writeup)
    
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
        read_time=writeup_service.calculate_read_time(saved_writeup.content),
    )


@router.post("/{writeup_id}/publish", response_model=WriteupResponseDTO)
async def publish_writeup(
    writeup_id: UUID,
    current_user: User = Depends(get_current_admin),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    writeup_service: WriteupService = Depends(get_writeup_service),
):
    """Publica un writeup (requiere autenticación)."""
    use_case = PublishWriteupUseCase(writeup_repo, writeup_service)
    
    try:
        result = use_case.execute(writeup_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Writeup not found",
            )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{writeup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_writeup(
    writeup_id: UUID,
    current_user: User = Depends(get_current_admin),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
):
    """Elimina un writeup (requiere admin)."""
    deleted = writeup_repo.delete(writeup_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writeup not found",
        )
