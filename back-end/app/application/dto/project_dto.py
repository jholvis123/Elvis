"""
DTOs para Proyectos.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl


class ProjectCreateDTO(BaseModel):
    """DTO para crear un proyecto."""
    
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Portfolio Backend",
                "description": "Backend API for portfolio website using Clean Architecture",
                "short_description": "FastAPI backend with Clean Architecture",
                "github_url": "https://github.com/user/portfolio-backend",
                "technologies": ["Python", "FastAPI", "SQLAlchemy"],
                "highlights": ["Clean Architecture", "JWT Auth", "REST API"]
            }
        }


class ProjectUpdateDTO(BaseModel):
    """DTO para actualizar un proyecto."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    technologies: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    featured: Optional[bool] = None
    order: Optional[int] = None


class ProjectResponseDTO(BaseModel):
    """DTO para respuesta de proyecto."""
    
    id: UUID
    title: str
    description: str
    short_description: Optional[str]
    image_url: Optional[str]
    github_url: Optional[str]
    demo_url: Optional[str]
    technologies: List[str]
    highlights: List[str]
    status: str
    featured: bool
    order: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProjectListResponseDTO(BaseModel):
    """DTO para lista paginada de proyectos."""
    
    items: List[ProjectResponseDTO]
    total: int
    page: int
    size: int
    pages: int


class ProjectSummaryDTO(BaseModel):
    """DTO resumido de proyecto (para cards)."""
    
    id: UUID
    title: str
    short_description: Optional[str]
    image_url: Optional[str]
    technologies: List[str]
    featured: bool
    
    class Config:
        from_attributes = True
