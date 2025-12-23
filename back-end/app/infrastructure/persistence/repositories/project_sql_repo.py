"""
Implementación SQL del repositorio de proyectos.
"""

import json
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....domain.entities.project import Project, ProjectStatus
from ....domain.repositories.project_repo import ProjectRepository
from ..models.project_model import ProjectModel


class ProjectSqlRepository(ProjectRepository):
    """Implementación SQL del repositorio de proyectos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, project: Project) -> Project:
        """Guarda un proyecto (crear o actualizar)."""
        project_id = str(project.id)
        existing = self.db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        
        if existing:
            existing.title = project.title
            existing.description = project.description
            existing.short_description = project.short_description
            existing.image_url = project.image_url
            existing.github_url = project.github_url
            existing.demo_url = project.demo_url
            existing.technologies = json.dumps(project.technologies)
            existing.highlights = json.dumps(project.highlights)
            existing.status = project.status.value
            existing.featured = project.featured
            existing.order = project.order
            existing.updated_at = project.updated_at
        else:
            db_project = ProjectModel(
                id=project_id,
                title=project.title,
                description=project.description,
                short_description=project.short_description,
                image_url=project.image_url,
                github_url=project.github_url,
                demo_url=project.demo_url,
                technologies=json.dumps(project.technologies),
                highlights=json.dumps(project.highlights),
                status=project.status.value,
                featured=project.featured,
                order=project.order,
                created_at=project.created_at,
            )
            self.db.add(db_project)
        
        self.db.commit()
        return project
    
    def get_by_id(self, project_id: UUID) -> Optional[Project]:
        """Obtiene un proyecto por su ID."""
        db_project = self.db.query(ProjectModel).filter(ProjectModel.id == str(project_id)).first()
        return self._to_entity(db_project) if db_project else None
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProjectStatus] = None,
    ) -> List[Project]:
        """Obtiene todos los proyectos con paginación y filtros."""
        query = self.db.query(ProjectModel)
        
        if status:
            query = query.filter(ProjectModel.status == status.value)
        
        db_projects = query.order_by(ProjectModel.order).offset(skip).limit(limit).all()
        return [self._to_entity(p) for p in db_projects]
    
    def get_featured(self, limit: int = 5) -> List[Project]:
        """Obtiene los proyectos destacados."""
        db_projects = (
            self.db.query(ProjectModel)
            .filter(ProjectModel.featured == True)
            .filter(ProjectModel.status == "published")
            .order_by(ProjectModel.order)
            .limit(limit)
            .all()
        )
        return [self._to_entity(p) for p in db_projects]
    
    def get_published(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Obtiene solo los proyectos publicados."""
        return self.get_all(skip=skip, limit=limit, status=ProjectStatus.PUBLISHED)
    
    def get_by_technology(self, technology: str) -> List[Project]:
        """Obtiene proyectos que usen una tecnología específica."""
        # SQLite doesn't support JSON queries well, so we filter in Python
        all_projects = self.get_published()
        return [p for p in all_projects if technology.lower() in [t.lower() for t in p.technologies]]
    
    def delete(self, project_id: UUID) -> bool:
        """Elimina un proyecto por su ID."""
        result = self.db.query(ProjectModel).filter(ProjectModel.id == str(project_id)).delete()
        self.db.commit()
        return result > 0
    
    def count(self, status: Optional[ProjectStatus] = None) -> int:
        """Cuenta el número de proyectos."""
        query = self.db.query(ProjectModel)
        if status:
            query = query.filter(ProjectModel.status == status.value)
        return query.count()
    
    def _to_entity(self, model: ProjectModel) -> Project:
        """Convierte un modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        return Project(
            id=UUIDType(model.id),
            title=model.title,
            description=model.description,
            short_description=model.short_description,
            image_url=model.image_url,
            github_url=model.github_url,
            demo_url=model.demo_url,
            technologies=json.loads(model.technologies) if model.technologies else [],
            highlights=json.loads(model.highlights) if model.highlights else [],
            status=ProjectStatus(model.status),
            featured=model.featured,
            order=model.order,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
