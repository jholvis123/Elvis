"""
Modelo SQLAlchemy para CTF.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, CHAR, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..base import Base


class CTFModel(Base):
    """Modelo de base de datos para CTFs."""
    
    __tablename__ = "ctfs"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    level = Column(String(20), nullable=False)  # easy, medium, hard, insane
    category = Column(String(20), nullable=False)  # web, pwn, reverse, crypto, forensics, misc, osint, stego
    platform = Column(String(100), nullable=False)  # HackTheBox, TryHackMe, Custom, etc.
    description = Column(Text)
    points = Column(Integer, default=0)
    solved = Column(Boolean, default=False)
    solved_at = Column(DateTime)
    machine_os = Column(String(50))
    # Campos alineados con frontend
    skills = Column(Text)  # JSON string - antes: tags
    hints = Column(Text)   # JSON string
    flag_hash = Column(String(64))  # SHA256 hash de la flag (o patrón regex si is_flag_regex=True)
    is_flag_regex = Column(Boolean, default=False)
    author = Column(String(100))
    solved_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Auditoría
    created_by_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    writeup = relationship("WriteupModel", back_populates="ctf", uselist=False)
    attachments = relationship("AttachmentModel", back_populates="ctf", cascade="all, delete-orphan")
    created_by = relationship("UserModel", foreign_keys=[created_by_id])
    updated_by = relationship("UserModel", foreign_keys=[updated_by_id])
    
    def __repr__(self) -> str:
        return f"<CTF {self.title}>"
