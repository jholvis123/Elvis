"""
Interfaces de repositorios del dominio.
Definen contratos que deben implementar los adaptadores.
"""

from .user_repo import UserRepository
from .project_repo import ProjectRepository
from .ctf_repo import CTFRepository
from .writeup_repo import WriteupRepository
from .attachment_repo import AttachmentRepository
from .contact_repo import ContactRepository
from .flag_submission_repo import FlagSubmissionRepository

__all__ = [
    "UserRepository",
    "ProjectRepository",
    "CTFRepository",
    "WriteupRepository",
    "AttachmentRepository",
    "ContactRepository",
    "FlagSubmissionRepository",
]
