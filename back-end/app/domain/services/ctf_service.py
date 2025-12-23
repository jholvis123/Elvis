"""
Servicio de dominio para CTFs.
Contiene reglas de negocio relacionadas con retos CTF.
"""

from typing import List, Optional
from uuid import UUID
from ..entities.ctf import CTF, CTFLevel, CTFCategory, CTFStatus
from ..repositories.ctf_repo import CTFRepository


class CTFService:
    """Servicio de dominio para lógica de CTFs."""
    
    def __init__(self, ctf_repository: CTFRepository):
        self.ctf_repository = ctf_repository
    
    def can_publish(self, ctf: CTF) -> tuple[bool, Optional[str]]:
        """
        Verifica si un CTF puede ser publicado.
        Retorna (puede_publicar, mensaje_error).
        """
        if not ctf.title or len(ctf.title.strip()) == 0:
            return False, "CTF must have a title"
        
        if not ctf.description:
            return False, "CTF must have a description"
        
        if ctf.status == CTFStatus.PUBLISHED:
            return False, "CTF is already published"
        
        return True, None
    
    def calculate_points(self, level: CTFLevel, solved_count: int = 0) -> int:
        """Calcula los puntos base de un CTF según su dificultad."""
        base_points = {
            CTFLevel.EASY: 20,
            CTFLevel.MEDIUM: 30,
            CTFLevel.HARD: 40,
            CTFLevel.INSANE: 50,
        }
        return base_points.get(level, 10)
    
    def get_level_distribution(self) -> dict:
        """Obtiene la distribución de CTFs por nivel."""
        stats = self.ctf_repository.get_statistics()
        return stats.get("by_level", {})
    
    def get_category_distribution(self) -> dict:
        """Obtiene la distribución de CTFs por categoría."""
        stats = self.ctf_repository.get_statistics()
        return stats.get("by_category", {})
    
    def filter_ctfs(
        self,
        level: Optional[CTFLevel] = None,
        category: Optional[CTFCategory] = None,
        platform: Optional[str] = None,
        solved: Optional[bool] = None,
    ) -> List[CTF]:
        """Filtra CTFs según múltiples criterios."""
        ctfs = self.ctf_repository.get_published()
        
        if level:
            ctfs = [c for c in ctfs if c.level == level]
        
        if category:
            ctfs = [c for c in ctfs if c.category == category]
        
        if platform:
            ctfs = [c for c in ctfs if c.platform.lower() == platform.lower()]
        
        if solved is not None:
            ctfs = [c for c in ctfs if c.solved == solved]
        
        return ctfs
    
    def validate_ctf_data(self, title: str, level: str, category: str) -> dict:
        """
        Valida los datos de un CTF.
        Retorna un diccionario con errores si los hay.
        """
        errors = {}
        
        if not title or len(title.strip()) < 3:
            errors["title"] = "Title must be at least 3 characters"
        
        if len(title) > 200:
            errors["title"] = "Title must be at most 200 characters"
        
        try:
            CTFLevel(level)
        except ValueError:
            errors["level"] = f"Invalid level. Must be one of: {[l.value for l in CTFLevel]}"
        
        try:
            CTFCategory(category)
        except ValueError:
            errors["category"] = f"Invalid category. Must be one of: {[c.value for c in CTFCategory]}"
        
        return errors
