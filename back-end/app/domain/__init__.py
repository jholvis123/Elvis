"""
Domain module - Corazón del sistema.
Contiene entidades puras, interfaces de repositorios y servicios de dominio.
"""

from .entities import User, Project, CTF, Writeup, Technology
from .repositories import UserRepository, ProjectRepository, CTFRepository, WriteupRepository

__all__ = [
    # Entities
    "User",
    "Project", 
    "CTF",
    "Writeup",
    "Technology",
    # Repositories
    "UserRepository",
    "ProjectRepository",
    "CTFRepository",
    "WriteupRepository",
]
