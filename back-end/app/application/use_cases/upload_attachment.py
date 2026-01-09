from datetime import datetime
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

from ...domain.entities.attachment import Attachment, AttachmentType
from ...domain.services.storage_service import StorageService
from ...domain.repositories.attachment_repo import AttachmentRepository
from ...application.dto.attachment_dto import AttachmentUploadResponseDTO

class UploadAttachmentUseCase:
    """Caso de uso para subir un archivo adjunto."""

    def __init__(
        self,
        storage_service: StorageService,
        attachment_repository: AttachmentRepository
    ):
        self.storage_service = storage_service
        self.attachment_repository = attachment_repository

    def execute(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        size: int,
        ctf_id: Optional[UUID] = None,
        uploaded_by: Optional[UUID] = None
    ) -> AttachmentUploadResponseDTO:
        # Validar tamaño y extensión aquí si se desea, o delegar al router/service
        
        # 1. Guardar archivo físicamente
        saved_filename = self.storage_service.save_file(file, filename)
        
        # Construir path relativo o URL (aquí asumimos local storage)
        # En una imp. real, el storage service podría devolver la URL completa
        file_path = str(self.storage_service.upload_dir / saved_filename)
        
        # 2. Crear entidad
        attachment_id = uuid4()
        attachment = Attachment(
            id=attachment_id,
            ctf_id=ctf_id,
            name=filename,
            type=AttachmentType.FILE,
            url=f"/api/v1/attachments/{attachment_id}/download",
            file_path=file_path,
            size=size,
            mime_type=content_type,
            created_at=datetime.utcnow(),
            uploaded_by=uploaded_by
        )
        
        # 3. Persistir metadatos
        saved = self.attachment_repository.save(attachment)
        
        return AttachmentUploadResponseDTO(
            id=saved.id,
            filename=saved.name,
            attachment_type=saved.type.value,
            url=saved.url,
            size=saved.size,
            mime_type=saved.mime_type or "application/octet-stream",
            message="Archivo subido exitosamente"
        )
