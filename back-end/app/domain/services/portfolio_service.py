"""
Servicio de dominio para Portfolio.
Contiene la lógica de negocio para datos del portfolio.
"""

from typing import List, Dict, Optional

from ..entities.portfolio import PortfolioProfile, Highlight
from ..entities.technology import Technology


class PortfolioService:
    """Servicio de dominio para lógica del portfolio."""
    
    # Datos por defecto del portfolio (pueden venir de BD o config)
    DEFAULT_PROFILE = PortfolioProfile(
        name="Elvis",
        title="Desarrollador Fullstack & Especialista en Ciberseguridad",
        bio="Construyo aplicaciones seguras y mantenibles con foco en rendimiento.",
        roles=[
            "Desarrollador Fullstack",
            "Especialista en Ciberseguridad",
            "CTF Player",
            "DevSecOps Engineer",
        ],
        stack_items=[
            "Angular", "Tailwind", ".NET", "Node.js", "Azure", "DevSecOps"
        ],
        about_points=[
            "Construyo aplicaciones seguras y mantenibles con foco en rendimiento.",
            "Integro prácticas de ciberseguridad desde el diseño hasta el despliegue.",
            "Disfruto escribir y compartir writeups y laboratorios prácticos.",
        ],
        highlights=[
            Highlight(label="Años de experiencia", value="05+", icon="calendar", order=0),
            Highlight(label="Proyectos entregados", value="25+", icon="folder", order=1),
            Highlight(label="CTF resueltos", value="60+", icon="flag", order=2),
        ],
        social_links={
            "email": "elvis.dev@mail.com",
            "linkedin": "https://linkedin.com/in/elvis",
            "github": "https://github.com/elvis",
        },
    )
    
    def get_profile(self) -> PortfolioProfile:
        """Obtiene el perfil del portfolio."""
        return self.DEFAULT_PROFILE
    
    def get_roles(self) -> List[str]:
        """Obtiene los roles del portfolio."""
        return self.DEFAULT_PROFILE.roles
    
    def get_stack_items(self) -> List[str]:
        """Obtiene los items del stack tecnológico."""
        return self.DEFAULT_PROFILE.stack_items
    
    def get_about_points(self) -> List[str]:
        """Obtiene los puntos del about."""
        return self.DEFAULT_PROFILE.about_points
    
    def get_highlights(self) -> List[Dict]:
        """Obtiene los highlights como diccionarios."""
        return [
            {
                "label": h.label,
                "value": h.value,
                "icon": h.icon,
            }
            for h in sorted(self.DEFAULT_PROFILE.highlights, key=lambda x: x.order)
        ]
    
    def get_contact_info(self) -> List[Dict]:
        """Obtiene la información de contacto."""
        contact_info = []
        social = self.DEFAULT_PROFILE.social_links
        
        if "email" in social:
            contact_info.append({
                "type": "email",
                "label": "Correo directo",
                "value": social["email"],
                "url": f"mailto:{social['email']}",
                "icon": "email",
            })
        
        if "linkedin" in social:
            contact_info.append({
                "type": "linkedin",
                "label": "Perfil profesional",
                "value": social["linkedin"].replace("https://", ""),
                "url": social["linkedin"],
                "icon": "linkedin",
            })
        
        if "github" in social:
            contact_info.append({
                "type": "github",
                "label": "Código y proyectos",
                "value": social["github"].replace("https://", ""),
                "url": social["github"],
                "icon": "github",
            })
        
        return contact_info
    
    def get_technologies_by_category(self, technologies: List[Technology]) -> Dict[str, List[Dict]]:
        """Agrupa tecnologías por categoría."""
        result: Dict[str, List[Dict]] = {}
        
        for tech in technologies:
            category = tech.category.value
            if category not in result:
                result[category] = []
            
            result[category].append({
                "name": tech.name,
                "icon": tech.icon,
                "proficiency": tech.proficiency,
            })
        
        return result
