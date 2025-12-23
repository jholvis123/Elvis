"""
Entidades del dominio.
Son objetos puros sin dependencias de framework.
"""

from .user import User
from .project import Project
from .ctf import CTF
from .writeup import Writeup
from .technology import Technology
from .attachment import Attachment, AttachmentType
from .contact import Contact, ContactStatus, ProjectType
from .flag_submission import FlagSubmission
from .portfolio import PortfolioProfile, Highlight

__all__ = [
    "User",
    "Project", 
    "CTF",
    "Writeup",
    "Technology",
    "Attachment",
    "AttachmentType",
    "Contact",
    "ContactStatus",
    "ProjectType",
    "FlagSubmission",
    "PortfolioProfile",
    "Highlight",
]
