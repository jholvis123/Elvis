"""add portfolio_experiences table

Revision ID: b7e4a1c290fd
Revises: a9b8c7d6e5f4
Create Date: 2026-09-15 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e4a1c290fd"
down_revision: Union[str, None] = "a9b8c7d6e5f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "portfolio_experiences" in existing:
        return
    op.create_table(
        "portfolio_experiences",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("start_date", sa.String(length=7), nullable=False),
        sa.Column("end_date", sa.String(length=7), nullable=True),
        sa.Column("current", sa.Boolean(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("highlights", sa.Text(), nullable=True),
        sa.Column("technologies", sa.Text(), nullable=True),
        sa.Column("links", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if "portfolio_experiences" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("portfolio_experiences")
