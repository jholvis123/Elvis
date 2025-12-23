"""
Modelo SQLAlchemy para Writeup.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..base import Base


class WriteupModel(Base):
    """Modelo de base de datos para writeups."""
    
    __tablename__ = "writeups"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    ctf_id = Column(CHAR(36), ForeignKey("ctfs.id"), nullable=True, unique=True)
    content = Column(Text, nullable=False)
    summary = Column(String(500))
    tools_used = Column(Text)  # JSON string
    techniques = Column(Text)  # JSON string
    attachments = Column(Text)  # JSON string
    status = Column(String(20), default="draft")
    views = Column(Integer, default=0)
    author_id = Column(CHAR(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relaciones
    ctf = relationship("CTFModel", back_populates="writeup")
    author = relationship("UserModel")
    
    def __repr__(self) -> str:
        return f"<Writeup {self.title}>"
