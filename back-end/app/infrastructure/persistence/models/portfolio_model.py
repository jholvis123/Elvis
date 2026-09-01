"""
Modelo SQLAlchemy para el perfil del portfolio (fila singleton).
"""

from sqlalchemy import Column, String, DateTime, Text, CHAR
from datetime import datetime
import uuid

from ..base import Base


class PortfolioProfileModel(Base):
    """Modelo de base de datos para el perfil del portfolio."""

    __tablename__ = "portfolio_profiles"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    title = Column(String(300), nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(500))
    roles = Column(Text)  # JSON list
    stack_items = Column(Text)  # JSON list
    about_points = Column(Text)  # JSON list
    highlights = Column(Text)  # JSON list of {label,value,icon,order}
    social_links = Column(Text)  # JSON object
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PortfolioProfile {self.name}>"
