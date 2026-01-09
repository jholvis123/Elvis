"""
Implementación SQL del repositorio de Attachments.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....domain.entities.attachment import Attachment, AttachmentType
from ....domain.repositories.attachment_repo import AttachmentRepository
from ..models.attachment_model import AttachmentModel


class AttachmentSqlRepository(AttachmentRepository):
    """Repositorio SQL para adjuntos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, attachment: Attachment) -> Attachment:
        """Guarda un adjunto."""
        attachment_id = str(attachment.id)
        existing = self.db.query(AttachmentModel).filter(AttachmentModel.id == attachment_id).first()
        
        if existing:
            existing.name = attachment.name
            existing.type = attachment.type.value
            existing.url = attachment.url
            existing.file_path = attachment.file_path
            existing.size = attachment.size
            existing.mime_type = attachment.mime_type
            existing.checksum = attachment.checksum
        else:
            db_attachment = AttachmentModel(
                id=attachment_id,
                name=attachment.name,
                type=attachment.type.value,
                ctf_id=str(attachment.ctf_id) if attachment.ctf_id else None,
                url=attachment.url,
                file_path=attachment.file_path,
                size=attachment.size,
                mime_type=attachment.mime_type,
                checksum=attachment.checksum,
                uploaded_by=str(attachment.uploaded_by) if attachment.uploaded_by else None,
                created_at=attachment.created_at,
            )
            self.db.add(db_attachment)
        
        self.db.commit()
        return attachment
    
    def get_by_id(self, attachment_id: UUID) -> Optional[Attachment]:
        """Obtiene un adjunto por su ID."""
        db_attachment = self.db.query(AttachmentModel).filter(
            AttachmentModel.id == str(attachment_id)
        ).first()
        return self._to_entity(db_attachment) if db_attachment else None
    
    def get_by_ctf_id(self, ctf_id: UUID) -> List[Attachment]:
        """Obtiene todos los adjuntos de un CTF."""
        db_attachments = self.db.query(AttachmentModel).filter(
            AttachmentModel.ctf_id == str(ctf_id)
        ).all()
        return [self._to_entity(a) for a in db_attachments]
    
    def delete(self, attachment_id: UUID) -> bool:
        """Elimina un adjunto."""
        result = self.db.query(AttachmentModel).filter(
            AttachmentModel.id == str(attachment_id)
        ).delete()
        self.db.commit()
        return result > 0
    
    def delete_by_ctf_id(self, ctf_id: UUID) -> int:
        """Elimina todos los adjuntos de un CTF."""
        result = self.db.query(AttachmentModel).filter(
            AttachmentModel.ctf_id == str(ctf_id)
        ).delete()
        self.db.commit()
        return result
    
    def _to_entity(self, model: AttachmentModel) -> Attachment:
        """Convierte un modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        return Attachment(
            id=UUIDType(model.id),
            name=model.name,
            type=AttachmentType(model.type),
            ctf_id=UUIDType(model.ctf_id) if model.ctf_id else None,
            url=model.url,
            file_path=model.file_path,
            size=model.size,
            mime_type=model.mime_type,
            checksum=model.checksum,
            uploaded_by=UUIDType(model.uploaded_by) if model.uploaded_by else None,
            created_at=model.created_at,
        )
