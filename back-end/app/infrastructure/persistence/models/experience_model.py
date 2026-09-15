"""
Modelo SQLAlchemy para entradas de experiencia / trayectoria (no empleos inventados).
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, CHAR
from datetime import datetime
import uuid

from ..base import Base


class ExperienceModel(Base):
    """Filas de GET /portfolio/experience."""

    __tablename__ = "portfolio_experiences"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    organization = Column(String(200), nullable=True)
    kind = Column(String(32), nullable=False)  # project | training | security
    location = Column(String(120), nullable=True)
    start_date = Column(String(7), nullable=False)  # YYYY-MM
    end_date = Column(String(7), nullable=True)
    current = Column(Boolean, default=False)
    summary = Column(Text, nullable=False)
    highlights = Column(Text)  # JSON list
    technologies = Column(Text)  # JSON list
    links = Column(Text)  # JSON object
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
