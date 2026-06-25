"""add categorization rules and seed categories

Revision ID: 20260625_0003
Revises: 20260625_0002
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260625_0003"
down_revision: Union[str, Sequence[str], None] = "20260625_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
CONFIDENCE = sa.Numeric(5, 4)

DEFAULT_CATEGORIES = (
    ("Moradia", "expense"),
    ("Alimentacao", "expense"),
    ("Delivery", "expense"),
    ("Transporte", "expense"),
    ("Tecnologia", "expense"),
    ("Educacao", "expense"),
    ("Saude", "expense"),
    ("Lazer", "expense"),
    ("Assinaturas", "expense"),
    ("Investimentos", "transfer"),
    ("Transferencias", "transfer"),
    ("Dividas", "expense"),
    ("Impostos/Taxas", "expense"),
    ("Previdencia", "investment"),
    ("Renda", "income"),
    ("Renda passiva", "income"),
    ("Outros", "expense"),
    ("Nao classificado", "expense"),
)


def upgrade() -> None:
    op.create_table(
        "categorization_rules",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("pattern", sa.Text(), nullable=False),
        sa.Column("match_type", sa.Text(), nullable=False, server_default=sa.text("'contains'")),
        sa.Column("category_id", UUID, sa.ForeignKey("app.categories.id"), nullable=False),
        sa.Column("transaction_type", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("confidence_score", CONFIDENCE, nullable=False, server_default="0.8000"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "pattern",
            "match_type",
            "transaction_type",
            "category_id",
            name="uq_app_categorization_rules_pattern",
        ),
        schema="app",
    )
    op.create_index(
        "ix_app_categorization_rules_category_id",
        "categorization_rules",
        ["category_id"],
        schema="app",
    )
    op.create_index(
        "ix_app_categorization_rules_priority",
        "categorization_rules",
        ["priority", "confidence_score"],
        schema="app",
    )

    bind = op.get_bind()
    for name, category_type in DEFAULT_CATEGORIES:
        bind.execute(
            sa.text(
                """
                insert into app.categories (name, type, is_system)
                values (:name, :type, true)
                on conflict (name, type)
                do update set is_system = true
                """
            ),
            {"name": name, "type": category_type},
        )


def downgrade() -> None:
    op.drop_index("ix_app_categorization_rules_priority", table_name="categorization_rules", schema="app")
    op.drop_index("ix_app_categorization_rules_category_id", table_name="categorization_rules", schema="app")
    op.drop_table("categorization_rules", schema="app")
