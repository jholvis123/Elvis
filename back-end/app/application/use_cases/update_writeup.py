"""
Caso de uso: Actualizar Writeup.
"""

from typing import Optional
from uuid import UUID

from ..dto.writeup_dto import WriteupUpdateDTO
from ...domain.entities.writeup import Writeup
from ...domain.repositories.writeup_repo import WriteupRepository
from ...domain.services.writeup_service import WriteupService


class UpdateWriteupUseCase:
    """Caso de uso para actualizar un writeup existente."""

    def __init__(
        self,
        writeup_repository: WriteupRepository,
        writeup_service: WriteupService,
    ):
        self.writeup_repository = writeup_repository
        self.writeup_service = writeup_service

    def execute(
        self,
        writeup_id: UUID,
        data: WriteupUpdateDTO,
    ) -> Optional[Writeup]:
        """
        Actualiza campos presentes en el DTO. Contrato HTTP (path + body) intacto.

        Returns:
            Writeup persistido o None si no existe.
        """
        writeup = self.writeup_repository.get_by_id(writeup_id)
        if not writeup:
            return None

        if data.title is not None:
            writeup.title = data.title
        if data.content is not None:
            writeup.update_content(data.content)
        if data.summary is not None:
            writeup.summary = data.summary
        if data.tools_used is not None:
            writeup.tools_used = data.tools_used
        if data.techniques is not None:
            writeup.techniques = data.techniques

        return self.writeup_repository.save(writeup)
