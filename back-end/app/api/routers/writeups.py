"""
Router de Writeups.
"""

from typing import Optional, List
from uuid import UUID
import os
import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
from ...domain.services.markdown_service import markdown_service, MarkdownRenderResult, TOCItem
from ...domain.services.file_validator import FileValidator, FileValidationError
from ...domain.services.storage_service import StorageService
from ..dependencies import (
    get_writeup_repository,
    get_ctf_repository,
    get_writeup_service,
    get_current_user,
    get_current_admin,
    get_storage_service,
)


# DTOs para Markdown
class MarkdownRenderRequest(BaseModel):
    """Request para renderizar Markdown."""
    content: str
    base_url: Optional[str] = ""


class TOCItemDTO(BaseModel):
    """DTO para item de tabla de contenidos."""
    id: str
    text: str
    level: int


class MarkdownRenderResponse(BaseModel):
    """Response del renderizado de Markdown."""
    html: str
    toc: List[TOCItemDTO]
    word_count: int
    read_time_minutes: int
    has_code_blocks: bool
    languages_used: List[str]


class ImageUploadResponse(BaseModel):
    """Response para subida de imagen."""
    url: str
    filename: str
    markdown: str

router = APIRouter(prefix="/writeups", tags=["Writeups"])

# Validador de imágenes (10MB máximo)
image_validator = FileValidator(
    allowed_extensions=['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
    max_size=10 * 1024 * 1024  # 10MB en bytes
)


# ==================== ENDPOINTS DE MARKDOWN ====================

@router.post("/render-markdown", response_model=MarkdownRenderResponse)
async def render_markdown(
    request: MarkdownRenderRequest,
    req: Request,
):
    """
    Renderiza contenido Markdown a HTML sanitizado.
    
    Procesa:
    - Callouts (:::info, :::warning, :::tip, etc.)
    - Syntax highlighting para bloques de código
    - Tablas, listas, blockquotes
    - Autolinks a CTFs, writeups y usuarios
    - Genera TOC automático
    
    Todo el procesamiento se hace en backend para seguridad.
    """
    base_url = request.base_url or str(req.base_url).rstrip('/')
    
    result = markdown_service.process_markdown(
        content=request.content,
        base_url=base_url
    )
    
    return MarkdownRenderResponse(
        html=result.html,
        toc=[TOCItemDTO(id=item.id, text=item.text, level=item.level) for item in result.toc],
        word_count=result.word_count,
        read_time_minutes=result.read_time_minutes,
        has_code_blocks=result.has_code_blocks,
        languages_used=result.languages_used
    )


@router.post(
    "/upload-image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_writeup_image(
    file: UploadFile = File(..., description="Imagen para el writeup"),
    current_user: User = Depends(get_current_admin),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Sube una imagen para usar en writeups.
    
    - Acepta: JPG, PNG, GIF, WebP, SVG
    - Tamaño máximo: 10MB
    - Valida magic bytes
    - Retorna URL y snippet Markdown listo para insertar
    """
    try:
        # Obtener tamaño del archivo
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        filename = file.filename or "image.png"
        content_type = file.content_type or "image/png"
        
        # Validar archivo
        try:
            extension, safe_mime = image_validator.validate_file(
                file=file.file,
                filename=filename,
                size=size,
                mime_type=content_type
            )
        except FileValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        
        # Reset file position
        file.file.seek(0)
        
        # Generar nombre único
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file.file.read()[:1024]).hexdigest()[:8]
        file.file.seek(0)
        
        safe_filename = f"writeup_{timestamp}_{file_hash}{extension}"
        
        # Guardar archivo
        saved_path = storage_service.save_file(
            file=file.file,
            filename=safe_filename,
            subfolder="writeup-images"
        )
        
        # Construir URL
        image_url = f"/uploads/writeup-images/{safe_filename}"
        
        # Crear snippet Markdown
        alt_text = os.path.splitext(filename)[0]
        markdown_snippet = f"![{alt_text}]({image_url})"
        
        return ImageUploadResponse(
            url=image_url,
            filename=safe_filename,
            markdown=markdown_snippet
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading image",
        )


# ==================== ENDPOINTS DE WRITEUPS ====================


def _build_writeup_response(
    writeup: Writeup,
    writeup_service: WriteupService,
    include_html: bool = True,
    base_url: str = ""
) -> WriteupResponseDTO:
    """Helper para construir WriteupResponseDTO con HTML renderizado."""
    from ...application.dto.writeup_dto import TOCItemDTO
    
    # Renderizar Markdown si se solicita
    content_html = None
    toc = []
    word_count = 0
    languages_used = []
    read_time = writeup_service.calculate_read_time(writeup.content)
    
    if include_html and writeup.content:
        render_result = markdown_service.process_markdown(
            content=writeup.content,
            base_url=base_url
        )
        content_html = render_result.html
        toc = [TOCItemDTO(id=item.id, text=item.text, level=item.level) 
               for item in render_result.toc]
        word_count = render_result.word_count
        languages_used = render_result.languages_used
        read_time = render_result.read_time_minutes
    
    return WriteupResponseDTO(
        id=writeup.id,
        title=writeup.title,
        ctf_id=writeup.ctf_id,
        content=writeup.content,
        content_html=content_html,
        summary=writeup.summary,
        tools_used=writeup.tools_used,
        techniques=writeup.techniques,
        attachments=writeup.attachments,
        status=writeup.status.value,
        views=writeup.views,
        author_id=writeup.author_id,
        created_at=writeup.created_at,
        updated_at=writeup.updated_at,
        published_at=writeup.published_at,
        read_time=read_time,
        word_count=word_count,
        toc=toc,
        languages_used=languages_used,
    )


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
    
    # Para listados no incluimos HTML (performance)
    items = [
        _build_writeup_response(w, writeup_service, include_html=False)
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
    writeup_service: WriteupService = Depends(get_writeup_service),
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
            read_time=writeup_service.calculate_read_time(w.content),
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
    writeup.views += 1  # Reflejar en respuesta
    
    return _build_writeup_response(writeup, writeup_service, include_html=True)


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
    writeup.views += 1  # Reflejar en respuesta
    
    return _build_writeup_response(writeup, writeup_service, include_html=True)


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
    
    return _build_writeup_response(saved_writeup, writeup_service, include_html=True)


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
