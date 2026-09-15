"""
Router de Portfolio - Información del perfil profesional.
"""

from typing import List
from datetime import datetime
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...application.dto.portfolio_dto import (
    PortfolioProfileDTO,
    HighlightDTO,
    ContactInfoDTO,
    ExperienceItemDTO,
    ExperienceListDTO,
    ExperienceLinksDTO,
    CapabilitySkillDTO,
    CapabilitiesDTO,
)
from ...core.database import get_db
from ...infrastructure.persistence.models.experience_model import ExperienceModel
from ...domain.entities.portfolio import PortfolioProfile, Highlight
from ...domain.entities.user import User
from ...domain.services.portfolio_service import PortfolioService
from ..dependencies import get_portfolio_service, get_current_admin


router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


def _profile_to_dto(profile: PortfolioProfile) -> PortfolioProfileDTO:
    """Misma forma de respuesta para GET y PUT /portfolio/profile."""
    return PortfolioProfileDTO(
        name=profile.name,
        title=profile.title,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        roles=profile.roles,
        stack_items=profile.stack_items,
        about_points=profile.about_points,
        highlights=[
            HighlightDTO(
                icon=h.icon,
                value=h.value,
                label=h.label,
            )
            for h in profile.highlights
        ],
        social_links=profile.social_links,
    )


def _dto_to_profile(data: PortfolioProfileDTO) -> PortfolioProfile:
    return PortfolioProfile(
        name=data.name,
        title=data.title,
        bio=data.bio,
        avatar_url=data.avatar_url,
        roles=list(data.roles),
        stack_items=list(data.stack_items),
        about_points=list(data.about_points),
        highlights=[
            Highlight(label=h.label, value=h.value, icon=h.icon, order=i)
            for i, h in enumerate(data.highlights)
        ],
        social_links=dict(data.social_links),
        updated_at=datetime.utcnow(),
    )


@router.get(
    "/profile",
    response_model=PortfolioProfileDTO,
    summary="Obtener perfil completo",
)
async def get_profile(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioProfileDTO:
    """
    Obtiene el perfil completo del portfolio incluyendo:
    - Roles
    - Stack tecnológico
    - Puntos sobre el autor
    - Highlights destacados
    - Información de contacto
    """
    return _profile_to_dto(portfolio_service.get_profile())


@router.put(
    "/profile",
    response_model=PortfolioProfileDTO,
    summary="Actualizar perfil (admin)",
)
async def update_profile(
    data: PortfolioProfileDTO,
    current_user: User = Depends(get_current_admin),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioProfileDTO:
    """
    Actualiza el perfil persistido. Requiere admin.

    Cookie sessions: CSRF vía header X-CSRF-Token + cookie csrf_token
    (middleware global). Misma forma de respuesta que GET /portfolio/profile.
    """
    saved = portfolio_service.update_profile(_dto_to_profile(data))
    return _profile_to_dto(saved)


@router.get(
    "/roles",
    response_model=List[str],
    summary="Obtener roles",
)
async def get_roles(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> List[str]:
    """
    Obtiene la lista de roles profesionales.
    Usado para la animación de texto rotativo en el hero.
    """
    return portfolio_service.get_roles()


@router.get(
    "/stack",
    response_model=List[str],
    summary="Obtener stack tecnológico",
)
async def get_stack(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> List[str]:
    """
    Obtiene la lista del stack tecnológico principal.
    """
    return portfolio_service.get_stack_items()


@router.get(
    "/about",
    response_model=List[str],
    summary="Obtener puntos sobre el autor",
)
async def get_about_points(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> List[str]:
    """
    Obtiene los puntos destacados de la sección "Sobre mí".
    """
    return portfolio_service.get_about_points()


@router.get(
    "/highlights",
    response_model=List[HighlightDTO],
    summary="Obtener highlights",
)
async def get_highlights(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> List[HighlightDTO]:
    """
    Obtiene los highlights/estadísticas destacadas.
    """
    highlights = portfolio_service.get_highlights()
    return [
        HighlightDTO(
            icon=h.get("icon"),
            value=h.get("value"),
            label=h.get("label"),
        )
        for h in highlights
    ]


@router.get(
    "/contact-info",
    response_model=ContactInfoDTO,
    summary="Obtener información de contacto",
)
async def get_contact_info(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> ContactInfoDTO:
    """
    Obtiene la información de contacto y redes sociales.
    """
    profile = portfolio_service.get_profile()
    social = profile.social_links

    return ContactInfoDTO(
        email=social.get("email", ""),
        github=social.get("github"),
        linkedin=social.get("linkedin"),
        twitter=social.get("twitter"),
    )


# Skills con evidencia en repos públicos jholvis123 (Elvis, Global-, fastapi-product, CTFd).
# No inventa .NET / Node / Azure aquí (pueden seguir en profile.stack_items).
EVIDENCED_SKILLS = [
    CapabilitySkillDTO(name="Angular", category="frontend"),
    CapabilitySkillDTO(name="TypeScript", category="frontend"),
    CapabilitySkillDTO(name="Python", category="backend"),
    CapabilitySkillDTO(name="FastAPI", category="backend"),
    CapabilitySkillDTO(name="JWT", category="security"),
    CapabilitySkillDTO(name="Docker", category="devops"),
    CapabilitySkillDTO(name="CI/CD", category="devops"),
    CapabilitySkillDTO(name="SQL Server", category="data"),
    CapabilitySkillDTO(name="PostgreSQL", category="data"),
]


def _experience_to_dto(row: ExperienceModel) -> ExperienceItemDTO:
    links_raw = json.loads(row.links) if row.links else {}
    return ExperienceItemDTO(
        id=row.id,
        title=row.title,
        organization=row.organization,
        kind=row.kind,
        location=row.location,
        start_date=row.start_date,
        end_date=row.end_date,
        current=bool(row.current),
        summary=row.summary,
        highlights=json.loads(row.highlights) if row.highlights else [],
        technologies=json.loads(row.technologies) if row.technologies else [],
        links=ExperienceLinksDTO(
            github=links_raw.get("github"),
            demo=links_raw.get("demo"),
        ),
        order=int(row.order or 0),
    )


@router.get(
    "/experience",
    response_model=ExperienceListDTO,
    summary="Trayectoria / experiencia (público)",
)
async def list_experience(
    db: Session = Depends(get_db),
) -> ExperienceListDTO:
    """Lista ordenada: proyectos, formación y seguridad aplicada (sin empleos inventados)."""
    rows = (
        db.query(ExperienceModel)
        .order_by(ExperienceModel.order.asc(), ExperienceModel.start_date.desc())
        .all()
    )
    return ExperienceListDTO(items=[_experience_to_dto(r) for r in rows])


@router.get(
    "/capabilities",
    response_model=CapabilitiesDTO,
    summary="Roles y skills con evidencia",
)
async def get_capabilities(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> CapabilitiesDTO:
    """roles = perfil; skills = evidencia de repos seed (ver docstring del DTO)."""
    return CapabilitiesDTO(
        roles=list(portfolio_service.get_roles()),
        skills=list(EVIDENCED_SKILLS),
    )
