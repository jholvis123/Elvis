"""
Modelo SQLAlchemy para HintUnlock.
"""

from datetime import datetime
import uuid

from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, UniqueConstraint

from ..base import Base


class HintUnlockModel(Base):
    """Pista desbloqueada por un jugador (una fila por usuario + CTF + índice)."""

    __tablename__ = "hint_unlocks"
    __table_args__ = (
        UniqueConstraint("user_id", "ctf_id", "hint_index", name="uq_hint_unlock"),
    )

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)
    ctf_id = Column(CHAR(36), ForeignKey("ctfs.id", ondelete="CASCADE"), nullable=False, index=True)
    hint_index = Column(Integer, nullable=False)
    cost = Column(Integer, nullable=False, default=0)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
