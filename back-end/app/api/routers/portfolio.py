"""
Router de Portfolio - Información del perfil profesional.
"""

from typing import List, Optional
from datetime import datetime
import json
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
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
    AvatarUploadResponseDTO,
    AvatarDeleteResponseDTO,
)
from ...core.database import get_db
from ...infrastructure.persistence.models.experience_model import ExperienceModel
from ...domain.entities.portfolio import PortfolioProfile, Highlight
from ...domain.entities.user import User
from ...domain.services.portfolio_service import PortfolioService
from ...domain.services.storage_service import StorageService
from ...domain.services.file_validator import FileValidator, FileValidationError
from ...infrastructure.storage.local_storage import FileSystemStorage
from ..dependencies import (
    get_portfolio_service,
    get_current_admin,
    get_storage_service,
)


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
# No inventa .NET / Node / Azure (tampoco en DEFAULT_PROFILE / stack_items).
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


# ---------------------------------------------------------------------------
# Avatar / logo upload (admin) + public file serving
# ---------------------------------------------------------------------------

AVATAR_MAX_BYTES = 2 * 1024 * 1024  # ~2MB
AVATAR_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
AVATAR_SUBFOLDER = "avatars"
# Public URL stored in profile.avatar_url after upload
AVATAR_PUBLIC_PREFIX = "/api/v1/portfolio/avatar/file/"
_AVATAR_FILE_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    r"\.(jpg|jpeg|png|webp)$",
    re.IGNORECASE,
)

avatar_validator = FileValidator(
    allowed_extensions=AVATAR_EXTENSIONS,
    max_size=AVATAR_MAX_BYTES,
)


def _is_local_avatar_url(url: Optional[str]) -> bool:
    return bool(url) and url.startswith(AVATAR_PUBLIC_PREFIX)


def _file_id_from_avatar_url(url: str) -> Optional[str]:
    if not _is_local_avatar_url(url):
        return None
    file_id = url[len(AVATAR_PUBLIC_PREFIX) :]
    if not _AVATAR_FILE_ID_RE.match(file_id):
        return None
    return file_id


def _delete_local_avatar_file(
    storage_service: StorageService, avatar_url: Optional[str]
) -> None:
    """Borra el archivo local si avatar_url apunta a nuestro GET público."""
    file_id = _file_id_from_avatar_url(avatar_url or "")
    if not file_id:
        return
    relative = f"{AVATAR_SUBFOLDER}/{file_id}"
    storage_service.delete_file(relative)


@router.post(
    "/avatar",
    response_model=AvatarUploadResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Subir avatar/logo (admin)",
)
async def upload_avatar(
    file: UploadFile = File(..., description="Imagen de avatar/logo (jpg/png/webp)"),
    current_user: User = Depends(get_current_admin),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> AvatarUploadResponseDTO:
    """
    Sube avatar/logo del portfolio (multipart field: `file`).

    - Solo admin (Bearer o cookie + CSRF).
    - Extensiones: jpg, jpeg, png, webp (máx ~2MB).
    - Valida magic bytes; rechaza exe/iso/pdf y demás.
    - Persiste en `uploads/avatars/` y actualiza `profile.avatar_url`.
    - GET público: `/api/v1/portfolio/avatar/file/{id}`.
    """
    _ = current_user  # authz via Depends
    try:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        filename = file.filename or "avatar.png"
        content_type = file.content_type or "application/octet-stream"

        try:
            extension, safe_mime = avatar_validator.validate_file(
                file=file.file,
                filename=filename,
                size=size,
                mime_type=content_type,
            )
        except FileValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        file.file.seek(0)

        # Reemplazar avatar local previo si existía
        profile = portfolio_service.get_profile()
        _delete_local_avatar_file(storage_service, profile.avatar_url)

        relative = storage_service.save_file(
            file=file.file,
            filename=f"avatar{extension}",
            subfolder=AVATAR_SUBFOLDER,
        )
        file_id = Path(relative).name
        avatar_url = f"{AVATAR_PUBLIC_PREFIX}{file_id}"

        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        portfolio_service.update_profile(profile)

        return AvatarUploadResponseDTO(
            avatar_url=avatar_url,
            id=file_id,
            filename=file_id,
            content_type=safe_mime,
            size=size,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading avatar",
        )


@router.delete(
    "/avatar",
    response_model=AvatarDeleteResponseDTO,
    summary="Eliminar avatar/logo (admin)",
)
async def delete_avatar(
    current_user: User = Depends(get_current_admin),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> AvatarDeleteResponseDTO:
    """Limpia `avatar_url` del perfil y borra el archivo local si aplica."""
    _ = current_user
    profile = portfolio_service.get_profile()
    _delete_local_avatar_file(storage_service, profile.avatar_url)
    profile.avatar_url = None
    profile.updated_at = datetime.utcnow()
    portfolio_service.update_profile(profile)
    return AvatarDeleteResponseDTO(avatar_url=None, message="Avatar eliminado")


@router.get(
    "/avatar/file/{file_id}",
    summary="Servir archivo de avatar (público)",
    response_class=FileResponse,
)
async def get_avatar_file(
    file_id: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> FileResponse:
    """
    Sirve el archivo de avatar por id (público, sin auth).

    `file_id` es el nombre en disco: `{uuid}.{ext}` (jpg|jpeg|png|webp).
    """
    if not _AVATAR_FILE_ID_RE.match(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )

    relative = f"{AVATAR_SUBFOLDER}/{file_id}"
    if isinstance(storage_service, FileSystemStorage):
        path = storage_service.resolve_path(relative)
    else:
        path = None

    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )

    ext = path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    return FileResponse(
        path=str(path),
        media_type=mime_map.get(ext, "application/octet-stream"),
        filename=path.name,
    )