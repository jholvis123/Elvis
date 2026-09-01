"""
Interfaz del repositorio de perfil de portfolio.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.portfolio import PortfolioProfile


class PortfolioRepository(ABC):
    """Contrato para persistir el perfil singleton del portfolio."""

    @abstractmethod
    def get(self) -> Optional[PortfolioProfile]:
        """Obtiene el perfil persistido, o None si aún no hay fila."""
        ...

    @abstractmethod
    def save(self, profile: PortfolioProfile) -> PortfolioProfile:
        """Crea o actualiza el perfil singleton."""
        ...
