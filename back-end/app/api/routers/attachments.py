"""
Router de Attachments - Archivos adjuntos para CTFs.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse

from ...application.dto.attachment_dto import (
    AttachmentCreateDTO,
    AttachmentResponseDTO,
    AttachmentListResponseDTO,
    AttachmentUploadResponseDTO,
)
from ...domain.entities.user import User
from ...domain.entities.attachment import Attachment, AttachmentType
from ...domain.services.attachment_service import AttachmentService
from ...domain.services.storage_service import StorageService
from ...domain.services.file_validator import FileValidator, FileValidationError
from ...domain.repositories.attachment_repo import AttachmentRepository
from ...application.use_cases.upload_attachment import UploadAttachmentUseCase
from ..dependencies import (
    get_attachment_service, 
    get_current_admin, 
    get_storage_service,
    get_attachment_repository
)


router = APIRouter(prefix="/attachments", tags=["Attachments"])

# Instancia del validador de archivos
file_validator = FileValidator()


@router.post(
    "/upload",
    response_model=AttachmentUploadResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Subir archivo adjunto",
)
async def upload_attachment(
    ctf_id: Optional[UUID] = Form(None, description="ID del CTF (opcional)"),
    file: UploadFile = File(..., description="Archivo a subir"),
    current_user: User = Depends(get_current_admin),
    storage_service: StorageService = Depends(get_storage_service),
    attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
) -> AttachmentUploadResponseDTO:
    """
    Sube un archivo adjunto.
    
    - Si se envía `ctf_id`, el archivo se asocia a ese CTF.
    - Si no, queda huérfano (para asociar luego al crear el CTF).
    
    Realiza validación de:
    - Extensión del archivo
    - Tamaño máximo
    - Magic bytes (contenido real coincide con extensión)
    - Tipo MIME
    """
    use_case = UploadAttachmentUseCase(storage_service, attachment_repo)
    
    try:
        # Obtener tamaño del archivo
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        filename = file.filename or "unknown"
        content_type = file.content_type or "application/octet-stream"
        
        # Validación completa del archivo
        try:
            extension, safe_mime = file_validator.validate_file(
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
        
        # Resetear posición del archivo después de validación
        file.file.seek(0)

        return use_case.execute(
            file=file.file,
            filename=filename,
            content_type=safe_mime,  # Usar MIME type seguro
            size=size,
            ctf_id=ctf_id,
            uploaded_by=current_user.id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading file",
        )


@router.post(
    "/url",
    response_model=AttachmentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar URL adjunta",
    dependencies=[Depends(get_current_admin)],
)
async def add_url_attachment(
    attachment_data: AttachmentCreateDTO,
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentResponseDTO:
    """Agrega una URL como adjunto (Admin)."""
    # ... (Misma lógica, o mover a UseCase si fuera necesario)
    from uuid import uuid4
    from datetime import datetime
    
    attachment = Attachment(
        id=uuid4(),
        ctf_id=attachment_data.ctf_id,
        filename=attachment_data.filename or attachment_data.url,
        type=AttachmentType(attachment_data.attachment_type),
        url=attachment_data.url,
        created_at=datetime.utcnow(),
    )
    
    saved = attachment_service.attachment_repo.save(attachment)
    return saved


@router.get(
    "/{attachment_id}/download",
    summary="Descargar archivo adjunto",
)
async def download_attachment(
    attachment_id: UUID,
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> FileResponse:
    """Descarga un archivo adjunto por su ID."""
    attachment = attachment_service.attachment_repo.get_by_id(attachment_id)
    
    if not attachment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    
    if attachment.type != AttachmentType.FILE:
        # Si es URL, redirigir? O devolver 400?
        # Para URL type, el frontend debería usar el link directo.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Not a file")
        
    if not attachment.file_path:
         raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File path missing")

    # Aquí podríamos usar StorageService.get_file_path() si abstraemos más
    import os
    if not os.path.exists(attachment.file_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found on server")
        
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.name,
        media_type=attachment.mime_type or "application/octet-stream",
    )
