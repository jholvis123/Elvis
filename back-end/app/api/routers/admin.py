"""
Router de administración.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...domain.entities.user import User
from ...domain.entities.writeup import WriteupStatus
from ...domain.entities.contact import ContactStatus
from ...domain.repositories.project_repo import ProjectRepository
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.contact_repo import ContactRepository
from ..dependencies import (
    get_current_admin,
    get_project_repository,
    get_writeup_repository,
    get_ctf_repository,
    get_contact_repository,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminStatsDTO(BaseModel):
    """Conteos agregados para el panel de administración."""

    projects: int
    writeups_published: int
    writeups_draft: int
    ctfs: int
    contact_pending: int
    contact_total: int


@router.get("/stats", response_model=AdminStatsDTO)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin),
    project_repo: ProjectRepository = Depends(get_project_repository),
    writeup_repo: WriteupRepository = Depends(get_writeup_repository),
    ctf_repo: CTFRepository = Depends(get_ctf_repository),
    contact_repo: ContactRepository = Depends(get_contact_repository),
) -> AdminStatsDTO:
    """Estadísticas agregadas para administradores."""
    return AdminStatsDTO(
        projects=project_repo.count(),
        writeups_published=writeup_repo.count(status=WriteupStatus.PUBLISHED),
        writeups_draft=writeup_repo.count(status=WriteupStatus.DRAFT),
        ctfs=ctf_repo.count(),
        contact_pending=contact_repo.count(status=ContactStatus.PENDING),
        contact_total=contact_repo.count(),
    )
