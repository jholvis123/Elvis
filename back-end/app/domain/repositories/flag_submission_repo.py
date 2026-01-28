"""
Repositorio abstracto para FlagSubmission.
Define la interfaz para registrar y consultar intentos de flags.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.flag_submission import FlagSubmission


class FlagSubmissionRepository(ABC):
    """Interfaz del repositorio de submissions de flags."""
    
    @abstractmethod
    def save(self, submission: FlagSubmission) -> FlagSubmission:
        """Guarda un intento de flag."""
        pass
    
    @abstractmethod
    def get_by_ctf_id(self, ctf_id: UUID) -> List[FlagSubmission]:
        """Obtiene todos los intentos de un CTF."""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> List[FlagSubmission]:
        """Obtiene todos los intentos de un usuario."""
        pass
    
    @abstractmethod
    def get_successful_by_ctf_id(self, ctf_id: UUID) -> List[FlagSubmission]:
        """Obtiene intentos exitosos de un CTF."""
        pass
    
    @abstractmethod
    def has_user_solved(self, ctf_id: UUID, user_id: UUID) -> bool:
        """Verifica si un usuario ya resolvió un CTF."""
        pass
    
    @abstractmethod
    def count_solvers(self, ctf_id: UUID) -> int:
        """Cuenta usuarios únicos que resolvieron un CTF."""
        pass
    
    @abstractmethod
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el ranking de usuarios por puntos de CTF.
        
        Returns:
            Lista de diccionarios con user_id, username, total_points, solved_count, rank
        """
        pass
    
    @abstractmethod
    def get_user_stats(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas de CTF de un usuario específico.
        
        Returns:
            Diccionario con total_points, solved_count, rank, solved_ctfs
        """
        pass
