"""Preserve CTF solved semantics without a schema or data rewrite.

Revision ID: c8a41e0b7d22
Revises: b7e4a1c290fd
Create Date: 2026-09-30 14:00:00.000000

solved and solved_at mean the owner (an admin) solved the challenge.
solved_count counts visitor correct submits only.
This revision adds no columns and does not rewrite existing rows.
Historical solved=true values stay as stored.
"""
from typing import Sequence, Union


revision: str = "c8a41e0b7d22"
down_revision: Union[str, None] = "b7e4a1c290fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
