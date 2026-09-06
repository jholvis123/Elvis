"""ensure portable schema for fresh Postgres (Render)

Revision ID: a9b8c7d6e5f4
Revises: f1a8c3d4e5b6
Create Date: 2026-09-06 15:00:00.000000

Idempotent: creates missing tables with portable SQLAlchemy types.
No-op on databases that already have the schema (typical local MySQL).
Initial revision 73af1314d471 was empty historically; this closes the gap for Render.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, None] = "f1a8c3d4e5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables(bind) -> set:
    return set(sa.inspect(bind).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    existing = _tables(bind)

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("is_admin", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    if "projects" not in existing:
        op.create_table(
            "projects",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("short_description", sa.String(length=300), nullable=True),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("github_url", sa.String(length=500), nullable=True),
            sa.Column("demo_url", sa.String(length=500), nullable=True),
            sa.Column("technologies", sa.Text(), nullable=True),
            sa.Column("highlights", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("featured", sa.Boolean(), nullable=True),
            sa.Column("order", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "ctfs" not in existing:
        op.create_table(
            "ctfs",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("level", sa.String(length=20), nullable=False),
            sa.Column("category", sa.String(length=20), nullable=False),
            sa.Column("platform", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("points", sa.Integer(), nullable=True),
            sa.Column("solved", sa.Boolean(), nullable=True),
            sa.Column("solved_at", sa.DateTime(), nullable=True),
            sa.Column("machine_os", sa.String(length=50), nullable=True),
            sa.Column("skills", sa.Text(), nullable=True),
            sa.Column("hints", sa.Text(), nullable=True),
            sa.Column("flag_hash", sa.String(length=64), nullable=True),
            sa.Column("is_flag_regex", sa.Boolean(), nullable=True),
            sa.Column("author", sa.String(length=100), nullable=True),
            sa.Column("solved_count", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("created_by_id", sa.CHAR(length=36), nullable=True),
            sa.Column("updated_by_id", sa.CHAR(length=36), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "writeups" not in existing:
        op.create_table(
            "writeups",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("ctf_id", sa.CHAR(length=36), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("summary", sa.String(length=500), nullable=True),
            sa.Column("tools_used", sa.Text(), nullable=True),
            sa.Column("techniques", sa.Text(), nullable=True),
            sa.Column("attachments", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("views", sa.Integer(), nullable=True),
            sa.Column("author_id", sa.CHAR(length=36), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["ctf_id"], ["ctfs.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("ctf_id"),
        )

    if "attachments" not in existing:
        op.create_table(
            "attachments",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("type", sa.String(length=20), nullable=False),
            sa.Column("ctf_id", sa.CHAR(length=36), nullable=True),
            sa.Column("url", sa.Text(), nullable=True),
            sa.Column("file_path", sa.Text(), nullable=True),
            sa.Column("size", sa.Integer(), nullable=True),
            sa.Column("mime_type", sa.String(length=100), nullable=True),
            sa.Column("checksum", sa.String(length=64), nullable=True),
            sa.Column("uploaded_by", sa.CHAR(length=36), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["ctf_id"], ["ctfs.id"]),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "contacts" not in existing:
        op.create_table(
            "contacts",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("project_type", sa.String(length=20), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("read_at", sa.DateTime(), nullable=True),
            sa.Column("replied_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "flag_submissions" not in existing:
        op.create_table(
            "flag_submissions",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("ctf_id", sa.CHAR(length=36), nullable=False),
            sa.Column("user_id", sa.CHAR(length=36), nullable=True),
            sa.Column("flag", sa.Text(), nullable=False),
            sa.Column("is_correct", sa.Boolean(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("submitted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["ctf_id"], ["ctfs.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    # portfolio_profiles may already exist via f1a8c3d4e5b6
    if "portfolio_profiles" not in existing:
        op.create_table(
            "portfolio_profiles",
            sa.Column("id", sa.CHAR(length=36), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("title", sa.String(length=300), nullable=False),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("avatar_url", sa.String(length=500), nullable=True),
            sa.Column("roles", sa.Text(), nullable=True),
            sa.Column("stack_items", sa.Text(), nullable=True),
            sa.Column("about_points", sa.Text(), nullable=True),
            sa.Column("highlights", sa.Text(), nullable=True),
            sa.Column("social_links", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    # Intentionally empty: dropping shared schema is unsafe for mixed MySQL/Postgres deploys.
    pass
