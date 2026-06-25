"""create initial database schemas

Revision ID: 20260625_0001
Revises:
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260625_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMAS = ("bronze", "silver", "gold", "app", "audit")


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))


def downgrade() -> None:
    for schema in reversed(SCHEMAS):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
