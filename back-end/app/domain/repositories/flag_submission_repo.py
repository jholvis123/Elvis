"""
Repositorio abstracto para FlagSubmission.
Define la interfaz para registrar y consultar intentos de flags.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.flag_submission import FlagSubmission
from ..entities.scoreboard import PlayerSolve


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
    def has_anonymous_correct_from_ip(self, ctf_id: UUID, ip_address: str) -> bool:
        """Verifica si ya hay un acierto anónimo de esa IP en el CTF."""
        pass
    
    @abstractmethod
    def count_solvers(self, ctf_id: UUID) -> int:
        """Cuenta usuarios únicos que resolvieron un CTF."""
        pass
    
    @abstractmethod
    def get_player_solves(
        self,
        ctf_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> List[PlayerSolve]:
        """
        Primer acierto por (jugador, CTF), solo jugadores activos no admin
        y CTFs publicados. Ordenado por solved_at ascendente.
        """
        pass
