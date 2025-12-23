"""
Modelo SQLAlchemy para User.
"""

from sqlalchemy import Column, String, Boolean, DateTime, CHAR
from datetime import datetime
import uuid

from ..base import Base


class UserModel(Base):
    """Modelo de base de datos para usuarios."""
    
    __tablename__ = "users"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
