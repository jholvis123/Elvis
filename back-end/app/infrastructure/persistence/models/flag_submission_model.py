"""
Modelo SQLAlchemy para FlagSubmission.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, CHAR, ForeignKey
from datetime import datetime
import uuid

from ..base import Base


class FlagSubmissionModel(Base):
    """Modelo de base de datos para intentos de flags."""
    
    __tablename__ = "flag_submissions"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ctf_id = Column(CHAR(36), ForeignKey("ctfs.id"), nullable=False)
    user_id = Column(CHAR(36), ForeignKey("users.id"))
    flag = Column(Text, nullable=False)  # Guardamos hash o la flag para auditoría
    is_correct = Column(Boolean, default=False)
    ip_address = Column(String(45))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<FlagSubmission ctf={self.ctf_id} correct={self.is_correct}>"
