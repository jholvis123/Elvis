"""
Router de Attachments - Archivos adjuntos para CTFs.
"""

import os
import shutil
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse

from ...application.dto.attachment_dto import (
    AttachmentCreateDTO,
    AttachmentResponseDTO,
    AttachmentListResponseDTO,
)
from ...domain.entities.attachment import Attachment, AttachmentType
from ...domain.services.attachment_service import AttachmentService
from ..dependencies import get_attachment_service, get_current_admin


router = APIRouter(prefix="/attachments", tags=["Attachments"])

# Configuración de uploads
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    ".zip", ".tar", ".gz", ".7z", ".rar",  # Archivos comprimidos
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",  # Imágenes
    ".pdf", ".txt", ".md", ".log",  # Documentos
    ".pcap", ".pcapng",  # Capturas de red
    ".bin", ".exe", ".elf", ".dll",  # Binarios
    ".py", ".js", ".c", ".cpp", ".java",  # Código fuente
}


def validate_file_extension(filename: str) -> bool:
    """Valida la extensión del archivo."""
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def ensure_upload_dir() -> str:
    """Asegura que el directorio de uploads existe."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    return UPLOAD_DIR


@router.post(
    "/upload",
    response_model=AttachmentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Subir archivo adjunto",
    dependencies=[Depends(get_current_admin)],
)
async def upload_attachment(
    ctf_id: UUID = Form(..., description="ID del CTF al que pertenece"),
    file: UploadFile = File(..., description="Archivo a subir"),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentResponseDTO:
    """
    Sube un archivo adjunto para un CTF (solo admin).
    
    Tipos de archivo permitidos:
    - Archivos comprimidos: .zip, .tar, .gz, .7z, .rar
    - Imágenes: .png, .jpg, .jpeg, .gif, .bmp
    - Documentos: .pdf, .txt, .md, .log
    - Capturas de red: .pcap, .pcapng
    - Binarios: .bin, .exe, .elf, .dll
    - Código fuente: .py, .js, .c, .cpp, .java
    """
    # Validar extensión
    if not file.filename or not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # Validar tamaño
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB",
        )
    
    # Generar nombre único
    upload_dir = ensure_upload_dir()
    ctf_dir = os.path.join(upload_dir, str(ctf_id))
    os.makedirs(ctf_dir, exist_ok=True)
    
    _, ext = os.path.splitext(file.filename)
    unique_filename = f"{uuid4()}{ext}"
    file_path = os.path.join(ctf_dir, unique_filename)
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo: {str(e)}",
        )
    
    # Crear registro en BD
    attachment = Attachment(
        id=uuid4(),
        ctf_id=ctf_id,
        filename=file.filename,
        attachment_type=AttachmentType.FILE,
        file_path=file_path,
        size=file_size,
        mime_type=file.content_type,
        created_at=datetime.utcnow(),
    )
    
    saved = attachment_service.attachment_repo.save(attachment)
    
    return AttachmentResponseDTO(
        id=saved.id,
        ctf_id=saved.ctf_id,
        filename=saved.filename,
        attachment_type=saved.attachment_type.value,
        url=f"/api/v1/attachments/{saved.id}/download",
        size=saved.size,
        mime_type=saved.mime_type,
        created_at=saved.created_at,
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
    """
    Agrega una URL como adjunto para un CTF (solo admin).
    
    Tipos soportados:
    - **url**: Enlace a recurso externo
    - **docker**: Imagen Docker para ejecutar
    """
    if attachment_data.attachment_type not in ["url", "docker"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para archivos use el endpoint /upload",
        )
    
    if not attachment_data.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL es requerida para este tipo de adjunto",
        )
    
    attachment = Attachment(
        id=uuid4(),
        ctf_id=attachment_data.ctf_id,
        filename=attachment_data.filename or attachment_data.url,
        attachment_type=AttachmentType(attachment_data.attachment_type),
        url=attachment_data.url,
        created_at=datetime.utcnow(),
    )
    
    saved = attachment_service.attachment_repo.save(attachment)
    
    return AttachmentResponseDTO(
        id=saved.id,
        ctf_id=saved.ctf_id,
        filename=saved.filename,
        attachment_type=saved.attachment_type.value,
        url=saved.url,
        created_at=saved.created_at,
    )


@router.get(
    "/ctf/{ctf_id}",
    response_model=AttachmentListResponseDTO,
    summary="Listar adjuntos de un CTF",
)
async def list_ctf_attachments(
    ctf_id: UUID,
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentListResponseDTO:
    """
    Lista todos los adjuntos de un CTF específico.
    """
    attachments = attachment_service.attachment_repo.get_by_ctf_id(ctf_id)
    
    return AttachmentListResponseDTO(
        items=[
            AttachmentResponseDTO(
                id=a.id,
                ctf_id=a.ctf_id,
                filename=a.filename,
                attachment_type=a.attachment_type.value,
                url=a.url if a.attachment_type != AttachmentType.FILE else f"/api/v1/attachments/{a.id}/download",
                size=a.size,
                mime_type=a.mime_type,
                created_at=a.created_at,
            )
            for a in attachments
        ],
        total=len(attachments),
    )


@router.get(
    "/{attachment_id}/download",
    summary="Descargar archivo adjunto",
)
async def download_attachment(
    attachment_id: UUID,
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> FileResponse:
    """
    Descarga un archivo adjunto por su ID.
    """
    attachment = attachment_service.attachment_repo.get_by_id(attachment_id)
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adjunto no encontrado",
        )
    
    if attachment.attachment_type != AttachmentType.FILE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este adjunto no es un archivo descargable",
        )
    
    if not attachment.file_path or not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor",
        )
    
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar adjunto",
    dependencies=[Depends(get_current_admin)],
)
async def delete_attachment(
    attachment_id: UUID,
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> None:
    """
    Elimina un adjunto y su archivo asociado (solo admin).
    """
    attachment = attachment_service.attachment_repo.get_by_id(attachment_id)
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adjunto no encontrado",
        )
    
    # Eliminar archivo físico si existe
    if attachment.file_path and os.path.exists(attachment.file_path):
        try:
            os.remove(attachment.file_path)
        except OSError:
            pass  # Log error but continue with DB deletion
    
    # Eliminar registro de BD
    attachment_service.attachment_repo.delete(attachment_id)
