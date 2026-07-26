"""Create initial Phase 1 schema.

Revision ID: 20260725_0001
Revises: None
Create Date: 2026-07-25
"""
from typing import Sequence, Union

from alembic import op

from app.database.base import Base
import app.models  # noqa: F401

revision: str = "20260725_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=False)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=False)
