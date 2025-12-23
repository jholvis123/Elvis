"""
Modelo SQLAlchemy para Attachment.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, CHAR, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..base import Base


class AttachmentModel(Base):
    """Modelo de base de datos para adjuntos."""
    
    __tablename__ = "attachments"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # file, url, docker
    ctf_id = Column(CHAR(36), ForeignKey("ctfs.id"), nullable=False)
    url = Column(Text)
    file_path = Column(Text)
    size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(64))
    uploaded_by = Column(CHAR(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    ctf = relationship("CTFModel", back_populates="attachments")
    uploader = relationship("UserModel", foreign_keys=[uploaded_by])
    
    def __repr__(self) -> str:
        return f"<Attachment {self.name}>"
