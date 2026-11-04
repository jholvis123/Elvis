"""
DTOs para Flag Submission.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, computed_field, model_validator


class FlagSubmitDTO(BaseModel):
    """DTO para enviar una flag."""
    
    flag: str = Field(..., min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "flag": "flag{example_flag_123}"
            }
        }


class FlagSubmitResponseDTO(BaseModel):
    """DTO para respuesta de submit de flag."""
    
    success: bool
    message: str
    points: Optional[int] = None
    already_solved: bool = False
    # Frontend (ctf.service.ts) lee is_correct; también se expone isCorrect.
    is_correct: Optional[bool] = None

    @model_validator(mode="after")
    def _sync_is_correct(self):
        if self.is_correct is None:
            self.is_correct = self.success
        return self

    @computed_field
    @property
    def isCorrect(self) -> bool:
        return bool(self.is_correct)


class SubmissionHistoryDTO(BaseModel):
    """DTO para historial de submissions."""
    
    id: UUID
    ctf_id: UUID
    is_correct: bool
    submitted_at: datetime
    
    class Config:
        from_attributes = True


# =============================================
# DTOs para Leaderboard / Ranking
# =============================================

class LeaderboardEntryDTO(BaseModel):
    """DTO para una entrada del leaderboard."""
    
    rank: int
    user_id: str
    username: str
    total_points: int
    solved_count: int
    hint_penalty: int = 0
    last_solve_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "hacker_pro",
                "total_points": 1500,
                "solved_count": 12
            }
        }


class LeaderboardResponseDTO(BaseModel):
    """DTO para respuesta del leaderboard completo."""
    
    entries: List[LeaderboardEntryDTO]
    total_players: int
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "entries": [
                    {"rank": 1, "user_id": "...", "username": "hacker1", "total_points": 1500, "solved_count": 12},
                    {"rank": 2, "user_id": "...", "username": "hacker2", "total_points": 1200, "solved_count": 10}
                ],
                "total_players": 50,
                "updated_at": "2026-01-28T12:00:00"
            }
        }


class SolvedCTFDTO(BaseModel):
    """DTO para un CTF resuelto por el usuario."""
    
    id: str
    title: str
    points: int
    category: str
    level: str
    solved_at: Optional[str] = None


class UserStatsDTO(BaseModel):
    """DTO para estadísticas de CTF de un usuario."""
    
    user_id: str
    username: str
    total_points: int
    solved_count: int
    rank: Optional[int] = None
    solved_ctfs: List[SolvedCTFDTO] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "hacker_pro",
                "total_points": 1500,
                "solved_count": 12,
                "rank": 3,
                "solved_ctfs": [
                    {"id": "...", "title": "Web Challenge 1", "points": 100, "category": "web", "level": "easy", "solved_at": "2026-01-20T10:30:00"}
                ]
            }
        }


class HintUnlockResponseDTO(BaseModel):
    """Respuesta al desbloquear una pista."""

    index: int
    hint: str
    cost: int
    already_unlocked: bool = False


class CTFSolveDTO(BaseModel):
    """Un jugador que resolvió un reto."""

    username: str
    solved_at: datetime
    first_blood: bool = False


class CTFSolvesResponseDTO(BaseModel):
    """Resoluciones de un reto, de la primera a la última."""

    items: List[CTFSolveDTO]
    total: int


class BoardChallengeDTO(BaseModel):
    """Casilla del tablero de retos."""

    id: UUID
    title: str
    level: str
    points: int
    solves: int
    solved_by_me: bool = False
    has_writeup: bool = False


class BoardCategoryDTO(BaseModel):
    category: str
    challenges: List[BoardChallengeDTO]


class BoardResponseDTO(BaseModel):
    """Tablero estilo CTFd: retos publicados y activos agrupados por categoría."""

    categories: List[BoardCategoryDTO]
    total: int
    solved_by_me: int = 0
    my_score: Optional[int] = None
    my_rank: Optional[int] = None
