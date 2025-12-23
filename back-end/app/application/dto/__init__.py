"""
Data Transfer Objects (DTOs) para la capa de aplicación.
"""

from .ctf_dto import CTFCreateDTO, CTFUpdateDTO, CTFResponseDTO, CTFListResponseDTO, CTFStatisticsDTO
from .writeup_dto import WriteupCreateDTO, WriteupUpdateDTO, WriteupResponseDTO
from .user_dto import UserCreateDTO, UserResponseDTO, TokenDTO
from .project_dto import ProjectCreateDTO, ProjectUpdateDTO, ProjectResponseDTO
from .contact_dto import ContactCreateDTO, ContactResponseDTO, ContactListResponseDTO, ProjectTypeDTO
from .attachment_dto import AttachmentCreateDTO, AttachmentResponseDTO, AttachmentListResponseDTO, AttachmentUploadResponseDTO
from .portfolio_dto import PortfolioProfileDTO, HighlightDTO, ContactInfoDTO
from .flag_dto import FlagSubmitDTO, FlagSubmitResponseDTO

__all__ = [
    # CTF
    "CTFCreateDTO",
    "CTFUpdateDTO",
    "CTFResponseDTO",
    "CTFListResponseDTO",
    "CTFStatisticsDTO",
    # Writeup
    "WriteupCreateDTO",
    "WriteupUpdateDTO",
    "WriteupResponseDTO",
    # User
    "UserCreateDTO",
    "UserResponseDTO",
    "TokenDTO",
    # Project
    "ProjectCreateDTO",
    "ProjectUpdateDTO",
    "ProjectResponseDTO",
    # Contact
    "ContactCreateDTO",
    "ContactResponseDTO",
    "ContactListResponseDTO",
    "ProjectTypeDTO",
    # Attachment
    "AttachmentCreateDTO",
    "AttachmentResponseDTO",
    "AttachmentListResponseDTO",
    "AttachmentUploadResponseDTO",
    # Portfolio
    "PortfolioProfileDTO",
    "HighlightDTO",
    "ContactInfoDTO",
    # Flag
    "FlagSubmitDTO",
    "FlagSubmitResponseDTO",
]
