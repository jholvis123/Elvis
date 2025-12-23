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
