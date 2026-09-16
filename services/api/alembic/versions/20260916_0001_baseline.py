"""Create or adopt the ApplyIntel applications schema.

Revision ID: 20260916_0001
Revises:
Create Date: 2026-09-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260916_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INDEX_COLUMNS = {
    "ix_applications_id": ["id"],
    "ix_applications_company": ["company"],
    "ix_applications_role": ["role"],
    "ix_applications_status": ["status"],
    "ix_applications_date_applied": ["date_applied"],
    "ix_applications_next_action_date": ["next_action_date"],
    "ix_applications_deleted_at": ["deleted_at"],
}


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "applications" not in inspector.get_table_names():
        op.create_table(
            "applications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("company", sa.String(length=200), nullable=False),
            sa.Column("role", sa.String(length=200), nullable=False),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("url", sa.String(length=500), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("date_applied", sa.Date(), nullable=False),
            sa.Column("next_action_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        existing_columns = {column["name"] for column in inspector.get_columns("applications")}
        if "next_action_date" not in existing_columns:
            op.add_column("applications", sa.Column("next_action_date", sa.Date(), nullable=True))
        if "deleted_at" not in existing_columns:
            op.add_column(
                "applications",
                sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            )

    inspector = sa.inspect(connection)
    existing_indexes = {index["name"] for index in inspector.get_indexes("applications")}
    for index_name, columns in INDEX_COLUMNS.items():
        if index_name not in existing_indexes:
            op.create_index(index_name, "applications", columns, unique=False)


def downgrade() -> None:
    op.drop_table("applications")
