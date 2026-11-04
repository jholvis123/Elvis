"""
Interfaz del repositorio de pistas desbloqueadas.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from ..entities.hint_unlock import HintUnlock


class HintUnlockRepository(ABC):
    """Contrato para persistir desbloqueos de pistas."""

    @abstractmethod
    def save(self, unlock: HintUnlock) -> HintUnlock:
        """Guarda un desbloqueo."""

    @abstractmethod
    def get(self, user_id: UUID, ctf_id: UUID, hint_index: int) -> Optional[HintUnlock]:
        """Obtiene el desbloqueo de una pista concreta, si existe."""

    @abstractmethod
    def unlocked_indexes(self, user_id: UUID, ctf_ids: List[UUID]) -> Dict[UUID, List[int]]:
        """Índices desbloqueados por el usuario, agrupados por CTF."""

    @abstractmethod
    def cost_by_user(self) -> Dict[UUID, int]:
        """Suma de costes de pistas desbloqueadas, por usuario."""
