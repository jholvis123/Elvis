"""
API layer - FastAPI routers y dependencias.
Este es el punto de entrada HTTP de la aplicación.
"""

from .routers import auth_router, ctf_router, projects_router, writeups_router

__all__ = [
    "auth_router",
    "ctf_router",
    "projects_router",
    "writeups_router",
]
