"""
Modelo SQLAlchemy para Project.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, CHAR
from datetime import datetime
import uuid

from ..base import Base


class ProjectModel(Base):
    """Modelo de base de datos para proyectos."""
    
    __tablename__ = "projects"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String(300))
    image_url = Column(String(500))
    github_url = Column(String(500))
    demo_url = Column(String(500))
    technologies = Column(Text)  # JSON string
    highlights = Column(Text)  # JSON string
    status = Column(String(20), default="draft")
    featured = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Project {self.title}>"
