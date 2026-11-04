"""
Value objects del ranking de jugadores (estilo CTFd).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class PlayerSolve:
    """Primer acierto de un jugador (no admin, activo) en un CTF publicado."""

    user_id: UUID
    username: str
    ctf_id: UUID
    ctf_title: str
    points: int
    category: str
    level: str
    solved_at: datetime


@dataclass
class ScoreEntry:
    """Fila del ranking: puntos de retos menos el coste de pistas desbloqueadas."""

    user_id: UUID
    username: str
    score: int = 0
    solved_count: int = 0
    hint_penalty: int = 0
    last_solve_at: Optional[datetime] = None
    rank: Optional[int] = None
    solves: List[PlayerSolve] = field(default_factory=list)
