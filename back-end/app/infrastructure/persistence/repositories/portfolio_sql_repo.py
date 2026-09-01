"""
Implementación SQL del repositorio de perfil de portfolio.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....domain.entities.portfolio import PortfolioProfile, Highlight
from ....domain.repositories.portfolio_repo import PortfolioRepository
from ..models.portfolio_model import PortfolioProfileModel


class PortfolioSqlRepository(PortfolioRepository):
    """Repositorio SQL para el perfil singleton del portfolio."""

    def __init__(self, db: Session):
        self.db = db

    def get(self) -> Optional[PortfolioProfile]:
        row = (
            self.db.query(PortfolioProfileModel)
            .order_by(PortfolioProfileModel.created_at.asc())
            .first()
        )
        return self._to_entity(row) if row else None

    def save(self, profile: PortfolioProfile) -> PortfolioProfile:
        row = (
            self.db.query(PortfolioProfileModel)
            .order_by(PortfolioProfileModel.created_at.asc())
            .first()
        )
        now = datetime.utcnow()
        payload = dict(
            name=profile.name,
            title=profile.title,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            roles=json.dumps(profile.roles or []),
            stack_items=json.dumps(profile.stack_items or []),
            about_points=json.dumps(profile.about_points or []),
            highlights=json.dumps(
                [
                    {
                        "label": h.label,
                        "value": h.value,
                        "icon": h.icon,
                        "order": h.order,
                    }
                    for h in (profile.highlights or [])
                ]
            ),
            social_links=json.dumps(profile.social_links or {}),
            updated_at=now,
        )
        if row:
            for key, value in payload.items():
                setattr(row, key, value)
        else:
            row = PortfolioProfileModel(
                id=str(profile.id),
                created_at=profile.created_at or now,
                **payload,
            )
            self.db.add(row)

        self.db.commit()
        self.db.refresh(row)
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: PortfolioProfileModel) -> PortfolioProfile:
        highlights_raw = json.loads(row.highlights or "[]")
        highlights = [
            Highlight(
                label=item.get("label", ""),
                value=item.get("value", ""),
                icon=item.get("icon"),
                order=item.get("order", idx),
            )
            for idx, item in enumerate(highlights_raw)
        ]
        return PortfolioProfile(
            id=UUID(row.id),
            name=row.name,
            title=row.title,
            bio=row.bio,
            avatar_url=row.avatar_url,
            roles=json.loads(row.roles or "[]"),
            stack_items=json.loads(row.stack_items or "[]"),
            about_points=json.loads(row.about_points or "[]"),
            highlights=highlights,
            social_links=json.loads(row.social_links or "{}"),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
