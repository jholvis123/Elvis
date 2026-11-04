"""
DTOs para CTFs.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

# Coste máximo de una pista (mismo techo que los puntos de un reto en CTFUpdateDTO)
MAX_HINT_COST = 1000


class AttachmentDTO(BaseModel):
    """DTO para adjuntos de CTF."""
    id: str
    name: str
    type: str  # file, url, docker
    url: str
    size: Optional[int] = None
    mime_type: Optional[str] = None


class CTFCreateDTO(BaseModel):
    """DTO para crear un CTF."""
    
    title: str = Field(..., min_length=3, max_length=200)
    level: str = Field(..., description="easy, medium, hard, insane")
    category: str = Field(..., description="web, pwn, reverse, crypto, forensics, misc, osint, stego")
    platform: Optional[str] = Field("Web", min_length=1, max_length=100)
    description: Optional[str] = None
    points: int = Field(default=0, ge=0, le=10000)
    machine_os: Optional[str] = None
    # Campos alineados con frontend
    skills: List[str] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)
    hint_costs: List[int] = Field(
        default_factory=list,
        description="Coste en puntos de cada pista (mismo índice que hints; falta = 0)",
    )
    flag: Optional[str] = Field(None, description="Flag del reto (se almacenará como hash o regex)")
    is_flag_regex: bool = Field(False, description="Si True, flag es un patrón Regex")
    author: Optional[str] = None
    is_active: bool = True
    attachments: List[AttachmentDTO] = Field(default_factory=list)
    
    @field_validator('skills', 'hints')
    @classmethod
    def remove_duplicates(cls, v: List[str]) -> List[str]:
        return list(dict.fromkeys(v)) if v else []

    @field_validator('hint_costs')
    @classmethod
    def validate_hint_costs(cls, v: List[int]) -> List[int]:
        return _validate_hint_costs(v) or []
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Auth Bypass 01",
                "level": "easy",
                "category": "web",
                "platform": "Custom",
                "description": "Un sistema de login vulnerable. Encuentra la forma de acceder sin credenciales válidas.",
                "points": 100,
                "skills": ["SQL Injection", "Cookies", "Sessions"],
                "hints": ["¿Has probado con comillas simples?", "El error SQL puede darte pistas"],
                "flag": "flag{sql_1nj3ct10n_b4s1c}",
                "author": "Elvis",
                "is_active": True
            }
        }


def _validate_hint_costs(v: Optional[List[int]]) -> Optional[List[int]]:
    if v is None:
        return None
    for cost in v:
        if cost < 0 or cost > MAX_HINT_COST:
            raise ValueError(f"hint cost must be between 0 and {MAX_HINT_COST}")
    return v


class CTFUpdateDTO(BaseModel):
    """DTO para actualizar un CTF."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    level: Optional[str] = None
    category: Optional[str] = None
    platform: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    points: Optional[int] = Field(None, ge=0, le=1000)
    machine_os: Optional[str] = None
    skills: Optional[List[str]] = None
    hints: Optional[List[str]] = None
    hint_costs: Optional[List[int]] = None
    flag: Optional[str] = None
    is_flag_regex: Optional[bool] = None
    author: Optional[str] = None
    is_active: Optional[bool] = None
    solved: Optional[bool] = None

    @field_validator('hint_costs')
    @classmethod
    def validate_hint_costs(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        return _validate_hint_costs(v)


class CTFResponseDTO(BaseModel):
    """DTO para respuesta de CTF."""
    
    id: UUID
    title: str
    level: str
    category: str
    platform: str
    description: Optional[str]
    points: int
    solved: bool
    solved_at: Optional[datetime]
    machine_os: Optional[str]
    # Campos alineados con frontend
    skills: List[str]
    # Pista bloqueada (coste > 0, no desbloqueada por quien consulta) → None
    hints: List[Optional[str]]
    hint_costs: List[int] = []
    unlocked_hints: List[int] = []
    author: Optional[str]
    solved_count: int
    is_active: bool
    attachments: List[AttachmentDTO] = []
    # Campos de sistema
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    has_writeup: bool = False
    
    class Config:
        from_attributes = True


class CTFListResponseDTO(BaseModel):
    """DTO para lista paginada de CTFs."""
    
    items: List[CTFResponseDTO]
    total: int
    page: int
    size: int
    pages: int


class CTFStatisticsDTO(BaseModel):
    """DTO para estadísticas de CTFs."""
    
    total: int
    solved: int
    total_points: int
    earned_points: int
    by_level: dict
    by_category: dict
    by_platform: dict
