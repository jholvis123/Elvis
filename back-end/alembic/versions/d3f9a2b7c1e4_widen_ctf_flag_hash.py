"""Widen ctfs.flag_hash so regex flag patterns fit.

Revision ID: d3f9a2b7c1e4
Revises: c8a41e0b7d22
Create Date: 2026-11-04 15:00:00.000000

flag_hash holds a SHA-256 hex digest (64 chars) for static flags, or the raw
regex pattern when is_flag_regex is true. 64 chars truncated or rejected
longer patterns on MySQL/PostgreSQL. Widen to 512 (MAX_FLAG_PATTERN_LENGTH).
batch_alter_table keeps this portable to SQLite.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d3f9a2b7c1e4"
down_revision: Union[str, None] = "c8a41e0b7d22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("ctfs") as batch_op:
        batch_op.alter_column(
            "flag_hash",
            existing_type=sa.String(length=64),
            type_=sa.String(length=512),
            existing_nullable=True,
        )


def downgrade() -> None:
    # Fails on MySQL/PostgreSQL if any stored regex pattern exceeds 64 chars.
    with op.batch_alter_table("ctfs") as batch_op:
        batch_op.alter_column(
            "flag_hash",
            existing_type=sa.String(length=512),
            type_=sa.String(length=64),
            existing_nullable=True,
        )
