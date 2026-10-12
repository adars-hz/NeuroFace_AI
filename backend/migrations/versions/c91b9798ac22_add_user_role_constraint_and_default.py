"""add user role constraint and default

Revision ID: c91b9798ac22
Revises: 1fccc53262f7
Create Date: 2026-10-12 11:41:20.058835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c91b9798ac22'
down_revision: Union[str, Sequence[str], None] = 'b32e33b6c8f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Add valid user roles and a database default for is_active."""

    op.create_check_constraint(
        "ck_users_valid_role",
        "users",
        "role IN ('ADMIN', 'TEACHER', 'STUDENT')",
    )

    op.alter_column(
        "users",
        "is_active",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("1"),
    )


def downgrade() -> None:
    """Remove the user role constraint and database default."""

    op.drop_constraint(
        "ck_users_valid_role",
        "users",
        type_="check",
    )

    op.alter_column(
        "users",
        "is_active",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=None,
    )
