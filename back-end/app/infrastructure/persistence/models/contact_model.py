"""
Modelo SQLAlchemy para Contact.
"""

from sqlalchemy import Column, String, DateTime, Text, CHAR
from datetime import datetime
import uuid

from ..base import Base


class ContactModel(Base):
    """Modelo de base de datos para mensajes de contacto."""
    
    __tablename__ = "contacts"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    project_type = Column(String(20), nullable=False)  # web, security, ctf, other
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, read, replied, archived
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    replied_at = Column(DateTime)
    
    def __repr__(self) -> str:
        return f"<Contact {self.name} - {self.email}>"
