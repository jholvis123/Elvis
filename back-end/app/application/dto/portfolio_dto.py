"""
DTOs para Portfolio.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel


class HighlightDTO(BaseModel):
    """DTO para highlight/estadística."""
    
    label: str
    value: str
    icon: Optional[str] = None


class ContactInfoDTO(BaseModel):
    """DTO para información de contacto."""
    
    email: str
    github: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None


class PortfolioProfileDTO(BaseModel):
    """DTO para perfil completo del portfolio."""
    
    name: str
    title: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str]
    stack_items: List[str]
    about_points: List[str]
    highlights: List[HighlightDTO]
    social_links: Dict[str, str]


class ProfileResponseDTO(BaseModel):
    """DTO para perfil del portfolio."""
    
    name: str
    title: str
    bio: Optional[str]
    avatar_url: Optional[str]
    roles: List[str]
    stack_items: List[str]
    about_points: List[str]
    highlights: List[HighlightDTO]
    contact_info: List[ContactInfoDTO]


class AboutResponseDTO(BaseModel):
    """DTO para sección about."""
    
    about_points: List[str]
    highlights: List[HighlightDTO]


class HeroResponseDTO(BaseModel):
    """DTO para sección hero."""
    
    name: str
    title: str
    roles: List[str]
    stack_items: List[str]


class TechnologyDTO(BaseModel):
    """DTO para tecnología."""
    
    name: str
    icon: Optional[str]
    category: str
    proficiency: int = 0


class TechnologiesResponseDTO(BaseModel):
    """DTO para lista de tecnologías."""
    
    items: List[TechnologyDTO]
    by_category: Dict[str, List[TechnologyDTO]]


class ExperienceLinksDTO(BaseModel):
    """Enlaces opcionales de una entrada de experiencia."""

    github: Optional[str] = None
    demo: Optional[str] = None


class ExperienceItemDTO(BaseModel):
    """Entrada pública de trayectoria (proyecto / formación / seguridad)."""

    id: str
    title: str
    organization: Optional[str] = None
    kind: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    current: bool = False
    summary: str
    highlights: List[str] = []
    technologies: List[str] = []
    links: ExperienceLinksDTO = ExperienceLinksDTO()
    order: int = 0


class ExperienceListDTO(BaseModel):
    """Lista ordenada de experiencia."""

    items: List[ExperienceItemDTO]


class CapabilitySkillDTO(BaseModel):
    """Skill con categoría (evidencia de repos reales)."""

    name: str
    category: str


class CapabilitiesDTO(BaseModel):
    """Roles + skills alineados a evidencia del portafolio.

    Roles: mismos que GET /portfolio/profile y /portfolio/roles.
    Skills: subset con evidencia en repos públicos seed (no inventa .NET/Node/Azure).
    """

    roles: List[str]
    skills: List[CapabilitySkillDTO]


class AvatarUploadResponseDTO(BaseModel):
    """Respuesta de POST /portfolio/avatar (multipart)."""

    avatar_url: str
    id: str
    filename: str
    content_type: str
    size: int


class AvatarDeleteResponseDTO(BaseModel):
    """Respuesta de DELETE /portfolio/avatar."""

    avatar_url: Optional[str] = None
    message: str = "Avatar eliminado"

