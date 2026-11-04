"""
Implementación SQL del repositorio de pistas desbloqueadas.
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ....domain.entities.hint_unlock import HintUnlock
from ....domain.repositories.hint_unlock_repo import HintUnlockRepository
from ..models.hint_unlock_model import HintUnlockModel


class HintUnlockSqlRepository(HintUnlockRepository):
    """Repositorio SQL para desbloqueos de pistas."""

    def __init__(self, db: Session):
        self.db = db

    def save(self, unlock: HintUnlock) -> HintUnlock:
        """Guarda un desbloqueo. Si ya existía (carrera), devuelve el existente."""
        self.db.add(
            HintUnlockModel(
                id=str(unlock.id),
                user_id=str(unlock.user_id),
                ctf_id=str(unlock.ctf_id),
                hint_index=unlock.hint_index,
                cost=unlock.cost,
                unlocked_at=unlock.unlocked_at,
            )
        )
        try:
            self.db.commit()
        except IntegrityError:
            # Restricción única: dos peticiones simultáneas no cobran dos veces
            self.db.rollback()
            existing = self.get(unlock.user_id, unlock.ctf_id, unlock.hint_index)
            if existing is None:
                raise
            return existing
        return unlock

    def get(self, user_id: UUID, ctf_id: UUID, hint_index: int) -> Optional[HintUnlock]:
        model = (
            self.db.query(HintUnlockModel)
            .filter(
                HintUnlockModel.user_id == str(user_id),
                HintUnlockModel.ctf_id == str(ctf_id),
                HintUnlockModel.hint_index == hint_index,
            )
            .first()
        )
        return self._to_entity(model) if model else None

    def unlocked_indexes(self, user_id: UUID, ctf_ids: List[UUID]) -> Dict[UUID, List[int]]:
        if not ctf_ids:
            return {}
        rows = (
            self.db.query(HintUnlockModel.ctf_id, HintUnlockModel.hint_index)
            .filter(
                HintUnlockModel.user_id == str(user_id),
                HintUnlockModel.ctf_id.in_([str(c) for c in ctf_ids]),
            )
            .all()
        )
        result: Dict[UUID, List[int]] = {}
        for ctf_id, index in rows:
            result.setdefault(UUID(ctf_id), []).append(index)
        for indexes in result.values():
            indexes.sort()
        return result

    def cost_by_user(self) -> Dict[UUID, int]:
        from sqlalchemy import func

        rows = (
            self.db.query(HintUnlockModel.user_id, func.sum(HintUnlockModel.cost))
            .group_by(HintUnlockModel.user_id)
            .all()
        )
        return {UUID(user_id): int(total or 0) for user_id, total in rows}

    @staticmethod
    def _to_entity(model: HintUnlockModel) -> HintUnlock:
        return HintUnlock(
            id=UUID(model.id),
            user_id=UUID(model.user_id),
            ctf_id=UUID(model.ctf_id),
            hint_index=model.hint_index,
            cost=model.cost or 0,
            unlocked_at=model.unlocked_at,
        )
