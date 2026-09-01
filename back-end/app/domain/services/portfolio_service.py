"""
Servicio de dominio para Portfolio.
Contiene la lógica de negocio para datos del portfolio.
"""

from typing import List, Dict, Optional

from ..entities.portfolio import PortfolioProfile, Highlight
from ..entities.technology import Technology
from ..repositories.portfolio_repo import PortfolioRepository


class PortfolioService:
    """Servicio de dominio para lógica del portfolio."""

    # Datos por defecto del portfolio (fallback si no hay fila persistida)
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

    def __init__(self, repository: Optional[PortfolioRepository] = None):
        self.repository = repository

    def _current(self) -> PortfolioProfile:
        """Perfil persistido si existe; si no, DEFAULT_PROFILE."""
        if self.repository is not None:
            stored = self.repository.get()
            if stored is not None:
                return stored
        return self.DEFAULT_PROFILE

    def get_profile(self) -> PortfolioProfile:
        """Obtiene el perfil del portfolio."""
        return self._current()

    def update_profile(self, profile: PortfolioProfile) -> PortfolioProfile:
        """Persiste el perfil. Requiere repositorio configurado."""
        if self.repository is None:
            raise RuntimeError("Portfolio persistence is not configured")
        return self.repository.save(profile)

    def get_roles(self) -> List[str]:
        """Obtiene los roles del portfolio."""
        return self._current().roles

    def get_stack_items(self) -> List[str]:
        """Obtiene los items del stack tecnológico."""
        return self._current().stack_items

    def get_about_points(self) -> List[str]:
        """Obtiene los puntos del about."""
        return self._current().about_points

    def get_highlights(self) -> List[Dict]:
        """Obtiene los highlights como diccionarios."""
        return [
            {
                "label": h.label,
                "value": h.value,
                "icon": h.icon,
            }
            for h in sorted(self._current().highlights, key=lambda x: x.order)
        ]

    def get_contact_info(self) -> List[Dict]:
        """Obtiene la información de contacto."""
        contact_info = []
        social = self._current().social_links

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
