"""
Router de Proyectos.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...application.dto.project_dto import (
    ProjectCreateDTO,
    ProjectUpdateDTO,
    ProjectResponseDTO,
    ProjectListResponseDTO,
    ProjectSummaryDTO,
)
from ...domain.entities.user import User
from ...domain.entities.project import Project, ProjectStatus
from ...domain.repositories.project_repo import ProjectRepository
from ...domain.services.project_service import ProjectService
from ..dependencies import (
    get_project_repository,
    get_project_service,
    get_current_user,
    get_current_admin,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/admin/all", response_model=ProjectListResponseDTO)
async def list_all_projects_admin(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    """Lista TODOS los proyectos para administradores (incluye drafts)."""
    skip = (page - 1) * size
    
    project_status = ProjectStatus(status) if status else None
    projects = project_repo.get_all(skip=skip, limit=size, status=project_status)
    total = project_repo.count(status=project_status)
    
    items = [
        ProjectResponseDTO(
            id=p.id,
            title=p.title,
            description=p.description,
            short_description=p.short_description,
            image_url=p.image_url,
            github_url=p.github_url,
            demo_url=p.demo_url,
            technologies=p.technologies,
            highlights=p.highlights,
            status=p.status.value,
            featured=p.featured,
            order=p.order,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]
    
    from math import ceil
    return ProjectListResponseDTO(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size > 0 else 0,
    )


@router.get("", response_model=ProjectListResponseDTO)
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    featured: Optional[bool] = None,
    technology: Optional[str] = None,
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    """Lista proyectos con filtros y paginación."""
    skip = (page - 1) * size
    
    if technology:
        projects = project_repo.get_by_technology(technology)
    elif featured:
        projects = project_repo.get_featured(limit=size)
    else:
        projects = project_repo.get_published(skip=skip, limit=size)
    
    total = project_repo.count(status=ProjectStatus.PUBLISHED)
    
    items = [
        ProjectResponseDTO(
            id=p.id,
            title=p.title,
            description=p.description,
            short_description=p.short_description,
            image_url=p.image_url,
            github_url=p.github_url,
            demo_url=p.demo_url,
            technologies=p.technologies,
            highlights=p.highlights,
            status=p.status.value,
            featured=p.featured,
            order=p.order,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]
    
    from math import ceil
    return ProjectListResponseDTO(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size > 0 else 0,
    )


@router.get("/featured", response_model=List[ProjectSummaryDTO])
async def get_featured_projects(
    limit: int = Query(5, ge=1, le=100),
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    """Obtiene los proyectos destacados."""
    projects = project_repo.get_featured(limit=limit)
    
    return [
        ProjectSummaryDTO(
            id=p.id,
            title=p.title,
            short_description=p.short_description,
            image_url=p.image_url,
            technologies=p.technologies,
            featured=p.featured,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/technologies")
async def get_technologies_summary(
    project_repo: ProjectRepository = Depends(get_project_repository),
    project_service: ProjectService = Depends(get_project_service),
):
    """Obtiene resumen de tecnologías usadas en proyectos."""
    return project_service.get_technologies_summary()


@router.get("/{project_id}", response_model=ProjectResponseDTO)
async def get_project(
    project_id: UUID,
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    """Obtiene un proyecto por su ID."""
    project = project_repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    return ProjectResponseDTO(
        id=project.id,
        title=project.title,
        description=project.description,
        short_description=project.short_description,
        image_url=project.image_url,
        github_url=project.github_url,
        demo_url=project.demo_url,
        technologies=project.technologies,
        highlights=project.highlights,
        status=project.status.value,
        featured=project.featured,
        order=project.order,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreateDTO,
    current_user: User = Depends(get_current_admin),
    project_repo: ProjectRepository = Depends(get_project_repository),
    project_service: ProjectService = Depends(get_project_service),
):
    """Crea un nuevo proyecto (requiere admin)."""
    # Validar datos
    errors = project_service.validate_project_data(data.title, data.description)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors,
        )
    
    # Crear proyecto
    project = Project(
        title=data.title,
        description=data.description,
        short_description=data.short_description,
        image_url=data.image_url,
        github_url=data.github_url,
        demo_url=data.demo_url,
        technologies=data.technologies,
        highlights=data.highlights,
    )
    
    saved_project = project_repo.save(project)
    
    return ProjectResponseDTO(
        id=saved_project.id,
        title=saved_project.title,
        description=saved_project.description,
        short_description=saved_project.short_description,
        image_url=saved_project.image_url,
        github_url=saved_project.github_url,
        demo_url=saved_project.demo_url,
        technologies=saved_project.technologies,
        highlights=saved_project.highlights,
        status=saved_project.status.value,
        featured=saved_project.featured,
        order=saved_project.order,
        created_at=saved_project.created_at,
        updated_at=saved_project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponseDTO)
async def update_project(
    project_id: UUID,
    data: ProjectUpdateDTO,
    current_user: User = Depends(get_current_admin),
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    """Actualiza un proyecto existente (requiere admin)."""
    project = project_repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Actualizar campos
    if data.title is not None:
        project.title = data.title
    if data.description is not None:
        project.description = data.description
    if data.short_description is not None:
        project.short_description = data.short_description
    if data.image_url is not None:
        project.image_url = data.image_url
    if data.github_url is not None:
        project.github_url = data.github_url
    if data.demo_url is not None:
        project.demo_url = data.demo_url
    if data.technologies is not None:
        project.technologies = data.technologies
    if data.highlights is not None:
        project.highlights = data.highlights
    if data.featured is not None:
        project.featured = data.featured
    if data.order is not None:
        project.order = data.order
    if data.status is not None:
        project.status = ProjectStatus(data.status)
    
    saved_project = project_repo.save(project)
    
    return ProjectResponseDTO(
        id=saved_project.id,
        title=saved_project.title,
        description=saved_project.description,
        short_description=saved_project.short_description,
        image_url=saved_project.image_url,
        github_url=saved_project.github_url,
        demo_url=saved_project.demo_url,
        technologies=saved_project.technologies,
        highlights=saved_project.highlights,
        status=saved_project.status.value,
        featured=saved_project.featured,
        order=saved_project.order,
        created_at=saved_project.created_at,
        updated_at=saved_project.updated_at,
    )


@router.post("/{project_id}/publish", response_model=ProjectResponseDTO)
async def publish_project(
    project_id: UUID,
    current_user: User = Depends(get_current_admin),
    project_repo: ProjectRepository = Depends(get_project_repository),
    project_service: ProjectService = Depends(get_project_service),
):
    """Publica un proyecto (requiere admin)."""
    project = project_repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    can_publish, error = project_service.can_publish(project)
    if not can_publish:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    project.publish()
    saved_project = project_repo.save(project)
    
    return ProjectResponseDTO(
        id=saved_project.id,
        title=saved_project.title,
        description=saved_project.description,
        short_description=saved_project.short_description,
        image_url=saved_project.image_url,
        github_url=saved_project.github_url,
        demo_url=saved_project.demo_url,
        technologies=saved_project.technologies,
        highlights=saved_project.highlights,
        status=saved_project.status.value,
        featured=saved_project.featured,
        order=saved_project.order,
        created_at=saved_project.created_at,
        updated_at=saved_project.updated_at,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_admin),
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    """Elimina un proyecto (requiere admin)."""
    deleted = project_repo.delete(project_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
