"""
Routers de la API.
"""

from .auth import router as auth_router
from .ctf import router as ctf_router
from .projects import router as projects_router
from .writeups import router as writeups_router
from .contact import router as contact_router
from .attachments import router as attachments_router
from .portfolio import router as portfolio_router

__all__ = [
    "auth_router",
    "ctf_router",
    "projects_router",
    "writeups_router",
    "contact_router",
    "attachments_router",
    "portfolio_router",
]
