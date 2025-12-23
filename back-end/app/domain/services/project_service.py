"""
Servicio de dominio para Proyectos.
Contiene reglas de negocio relacionadas con proyectos del portafolio.
"""

from typing import List, Optional
from ..entities.project import Project, ProjectStatus
from ..repositories.project_repo import ProjectRepository


class ProjectService:
    """Servicio de dominio para lógica de proyectos."""
    
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    def can_publish(self, project: Project) -> tuple[bool, Optional[str]]:
        """
        Verifica si un proyecto puede ser publicado.
        Retorna (puede_publicar, mensaje_error).
        """
        if not project.title or len(project.title.strip()) == 0:
            return False, "Project must have a title"
        
        if not project.description or len(project.description.strip()) < 50:
            return False, "Project description must be at least 50 characters"
        
        if project.status == ProjectStatus.PUBLISHED:
            return False, "Project is already published"
        
        return True, None
    
    def can_feature(self, project: Project) -> tuple[bool, Optional[str]]:
        """
        Verifica si un proyecto puede ser destacado.
        Retorna (puede_destacar, mensaje_error).
        """
        if project.status != ProjectStatus.PUBLISHED:
            return False, "Only published projects can be featured"
        
        if not project.image_url:
            return False, "Featured projects must have an image"
        
        return True, None
    
    def validate_project_data(self, title: str, description: str) -> dict:
        """
        Valida los datos de un proyecto.
        Retorna un diccionario con errores si los hay.
        """
        errors = {}
        
        if not title or len(title.strip()) < 3:
            errors["title"] = "Title must be at least 3 characters"
        
        if len(title) > 200:
            errors["title"] = "Title must be at most 200 characters"
        
        if not description or len(description.strip()) < 10:
            errors["description"] = "Description must be at least 10 characters"
        
        if len(description) > 5000:
            errors["description"] = "Description must be at most 5000 characters"
        
        return errors
    
    def get_technologies_summary(self) -> dict:
        """Obtiene un resumen de tecnologías usadas en proyectos."""
        projects = self.project_repository.get_published()
        
        tech_count = {}
        for project in projects:
            for tech in project.technologies:
                tech_count[tech] = tech_count.get(tech, 0) + 1
        
        return dict(sorted(tech_count.items(), key=lambda x: x[1], reverse=True))
    
    def reorder_projects(self, project_ids: List[str]) -> bool:
        """
        Reordena los proyectos según el orden de IDs proporcionado.
        """
        for order, project_id in enumerate(project_ids):
            project = self.project_repository.get_by_id(project_id)
            if project:
                project.order = order
                self.project_repository.save(project)
        
        return True
