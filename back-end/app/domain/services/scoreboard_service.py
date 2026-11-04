"""
Servicio de dominio del ranking de jugadores (estilo CTFd).

Puntuación = suma de puntos de los CTFs publicados resueltos
             − coste de las pistas desbloqueadas.
Empate: gana quien alcanzó su puntuación antes (último acierto más antiguo).
Admins e inactivos no aparecen.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import UUID

from ..entities.scoreboard import PlayerSolve, ScoreEntry
from ..repositories.flag_submission_repo import FlagSubmissionRepository
from ..repositories.hint_unlock_repo import HintUnlockRepository


class ScoreboardService:
    def __init__(
        self,
        submission_repository: FlagSubmissionRepository,
        hint_unlock_repository: HintUnlockRepository,
    ):
        self.submission_repository = submission_repository
        self.hint_unlock_repository = hint_unlock_repository

    def ranking(self) -> List[ScoreEntry]:
        """Ranking completo, con `rank` asignado (1 = primero)."""
        entries: Dict[UUID, ScoreEntry] = {}
        for solve in self.submission_repository.get_player_solves():
            entry = entries.setdefault(
                solve.user_id, ScoreEntry(user_id=solve.user_id, username=solve.username)
            )
            entry.solves.append(solve)
            entry.solved_count += 1
            entry.score += solve.points
            if entry.last_solve_at is None or solve.solved_at > entry.last_solve_at:
                entry.last_solve_at = solve.solved_at

        penalties = self.hint_unlock_repository.cost_by_user()
        for entry in entries.values():
            entry.hint_penalty = penalties.get(entry.user_id, 0)
            entry.score -= entry.hint_penalty

        ordered = sorted(
            entries.values(),
            key=lambda e: (-e.score, e.last_solve_at or datetime.max, e.username.lower()),
        )
        for rank, entry in enumerate(ordered, start=1):
            entry.rank = rank
        return ordered

    def user_entry(self, user_id: UUID) -> Optional[ScoreEntry]:
        """Fila del ranking de un jugador, o None si aún no resolvió nada."""
        for entry in self.ranking():
            if entry.user_id == user_id:
                return entry
        return None

    def ctf_solves(self, ctf_id: UUID) -> List[PlayerSolve]:
        """Jugadores que resolvieron el CTF, del primero (primera sangre) al último."""
        return self.submission_repository.get_player_solves(ctf_id=ctf_id)

    def solved_ctf_ids(self, user_id: UUID) -> Set[UUID]:
        return {s.ctf_id for s in self.submission_repository.get_player_solves(user_id=user_id)}

    def solve_counts(self) -> Dict[UUID, int]:
        counts: Dict[UUID, int] = {}
        for solve in self.submission_repository.get_player_solves():
            counts[solve.ctf_id] = counts.get(solve.ctf_id, 0) + 1
        return counts
