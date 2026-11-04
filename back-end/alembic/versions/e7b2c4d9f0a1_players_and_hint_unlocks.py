"""Players with alias only, hint costs and hint unlocks.

Revision ID: e7b2c4d9f0a1
Revises: d3f9a2b7c1e4
Create Date: 2026-11-04 17:30:00.000000

- users.email becomes nullable: CTF players register with alias + password.
  UNIQUE allows several NULLs on MySQL, PostgreSQL and SQLite.
- ctfs.hint_costs: JSON list[int] aligned with ctfs.hints (NULL = all free).
- hint_unlocks: one row per (user, ctf, hint index), with the cost paid.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e7b2c4d9f0a1"
down_revision: Union[str, None] = "d3f9a2b7c1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            nullable=True,
        )

    ctf_cols = {c["name"] for c in inspector.get_columns("ctfs")}
    if "hint_costs" not in ctf_cols:
        op.add_column("ctfs", sa.Column("hint_costs", sa.Text(), nullable=True))

    if "hint_unlocks" not in inspector.get_table_names():
        op.create_table(
            "hint_unlocks",
            sa.Column("id", sa.CHAR(length=36), primary_key=True),
            sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column(
                "ctf_id",
                sa.CHAR(length=36),
                sa.ForeignKey("ctfs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("hint_index", sa.Integer(), nullable=False),
            sa.Column("cost", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("unlocked_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("user_id", "ctf_id", "hint_index", name="uq_hint_unlock"),
        )
        op.create_index("ix_hint_unlocks_user_id", "hint_unlocks", ["user_id"])
        op.create_index("ix_hint_unlocks_ctf_id", "hint_unlocks", ["ctf_id"])


def downgrade() -> None:
    op.drop_index("ix_hint_unlocks_ctf_id", table_name="hint_unlocks")
    op.drop_index("ix_hint_unlocks_user_id", table_name="hint_unlocks")
    op.drop_table("hint_unlocks")
    op.drop_column("ctfs", "hint_costs")
    # Fails if alias-only players (email NULL) exist: delete or give them an email first.
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            nullable=False,
        )
