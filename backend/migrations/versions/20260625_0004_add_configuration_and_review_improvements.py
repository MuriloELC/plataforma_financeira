"""add configuration and review improvements

Revision ID: 20260625_0004
Revises: 20260625_0003
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260625_0004"
down_revision: Union[str, Sequence[str], None] = "20260625_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB
RATE = sa.Numeric(14, 6)


REFERENCE_OPTIONS = (
    ("card_brand", "visa", "Visa"),
    ("card_brand", "mastercard", "Mastercard"),
    ("card_brand", "elo", "Elo"),
    ("card_brand", "american_express", "American Express"),
    ("card_brand", "hipercard", "Hipercard"),
    ("investment_class", "cdb", "CDB"),
    ("investment_class", "fund", "Fundo"),
    ("investment_class", "alternative", "Alternativo"),
    ("investment_class", "pension", "Previdencia"),
    ("investment_class", "acao", "Acao"),
    ("investment_class", "etf", "ETF"),
    ("investment_class", "fii", "FII"),
    ("investment_class", "renda_fixa", "Renda fixa"),
    ("investment_product", "cdb", "CDB"),
    ("investment_product", "tesouro_selic", "Tesouro Selic"),
    ("liquidity", "daily", "Diaria"),
    ("liquidity", "d1", "D+1"),
    ("liquidity", "d30", "D+30"),
    ("liquidity", "maturity", "No vencimento"),
    ("liquidity", "illiquid", "Iliquido"),
    ("liquidity", "custom", "Personalizada"),
    ("rate_type", "fixed", "Prefixada"),
    ("rate_type", "post_fixed", "Pos-fixada"),
    ("rate_type", "indexed", "Indexada"),
    ("rate_type", "compound", "Composta"),
    ("rate_index", "cdi", "CDI"),
    ("rate_index", "selic", "Selic"),
    ("rate_index", "ipca", "IPCA"),
    ("rate_index", "fixed", "Fixa"),
    ("rate_periodicity", "monthly", "Mensal"),
    ("rate_periodicity", "annual", "Anual"),
    ("account_type", "checking", "Conta corrente"),
    ("account_type", "wallet", "Carteira"),
    ("account_type", "investment", "Investimento"),
    ("account_type", "cash", "Dinheiro"),
    ("import_source_type", "mercado_livre_account_statement_csv", "Mercado Livre CSV"),
    ("import_source_type", "mercado_livre_manual_cdb_csv", "Mercado Livre CDB CSV"),
    ("import_source_type", "manual_investment_csv", "Investimentos manual CSV"),
    ("import_source_type", "b3_monthly_consolidated_xlsx", "B3 mensal XLSX"),
    ("import_source_type", "b3_annual_consolidated_xlsx", "B3 anual XLSX"),
    ("import_source_type", "sicoob_checking_statement_pdf", "Sicoob extrato PDF"),
    ("import_source_type", "sicoob_card_invoice_pdf", "Sicoob fatura PDF"),
    ("import_source_type", "sicoob_investments_pdf", "Sicoob investimentos PDF"),
    ("import_source_type", "sicoob_payroll_pdf", "Contracheque PDF"),
)

INSTITUTIONS = (
    ("Sicoob", "bank"),
    ("Mercado Livre", "wallet"),
    ("Mercado Pago", "wallet"),
    ("B3", "broker"),
    ("Manual", "other"),
)


def upgrade() -> None:
    op.create_table(
        "reference_options",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("option_group", sa.Text(), nullable=False),
        sa.Column("option_key", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("option_group", "option_key", name="uq_app_reference_options_group_key"),
        schema="app",
    )
    op.create_index(
        "ix_app_reference_options_group_active",
        "reference_options",
        ["option_group", "is_active"],
        schema="app",
    )
    op.execute(
        """
        with duplicated as (
            select
                id,
                row_number() over (partition by name order by created_at, id) as row_number
            from app.institutions
        )
        update app.institutions institution
        set
            name = institution.name || ' (' || left(institution.id::text, 8) || ')',
            is_active = false
        from duplicated
        where duplicated.id = institution.id
          and duplicated.row_number > 1
        """
    )
    op.create_unique_constraint("uq_app_institutions_name", "institutions", ["name"], schema="app")

    op.add_column("cards", sa.Column("institution_id", UUID, sa.ForeignKey("app.institutions.id"), nullable=True), schema="silver")
    op.add_column("cards", sa.Column("brand_id", UUID, sa.ForeignKey("app.reference_options.id"), nullable=True), schema="silver")
    op.add_column("cards", sa.Column("is_virtual", sa.Boolean(), nullable=False, server_default=sa.false()), schema="silver")
    op.create_index("ix_silver_cards_institution_id", "cards", ["institution_id"], schema="silver")
    op.create_index("ix_silver_cards_brand_id", "cards", ["brand_id"], schema="silver")

    op.add_column("manual_investment_positions", sa.Column("product_id", UUID, sa.ForeignKey("app.reference_options.id"), nullable=True), schema="silver")
    op.add_column("manual_investment_positions", sa.Column("rate_type", sa.Text(), nullable=True), schema="silver")
    op.add_column("manual_investment_positions", sa.Column("rate_index", sa.Text(), nullable=True), schema="silver")
    op.add_column("manual_investment_positions", sa.Column("rate_percent", RATE, nullable=True), schema="silver")
    op.add_column("manual_investment_positions", sa.Column("rate_spread", RATE, nullable=True), schema="silver")
    op.add_column("manual_investment_positions", sa.Column("rate_periodicity", sa.Text(), nullable=True), schema="silver")
    op.add_column("manual_investment_positions", sa.Column("liquidity_type", sa.Text(), nullable=True), schema="silver")
    op.create_index("ix_silver_manual_investment_positions_product_id", "manual_investment_positions", ["product_id"], schema="silver")

    bind = op.get_bind()
    for name, institution_type in INSTITUTIONS:
        bind.execute(
            sa.text(
                """
                insert into app.institutions (name, institution_type, is_active)
                values (:name, :institution_type, true)
                on conflict do nothing
                """
            ),
            {"name": name, "institution_type": institution_type},
        )
    for option_group, option_key, label in REFERENCE_OPTIONS:
        bind.execute(
            sa.text(
                """
                insert into app.reference_options (option_group, option_key, label, is_system, is_active)
                values (:option_group, :option_key, :label, true, true)
                on conflict (option_group, option_key)
                do update set label = excluded.label, is_system = true
                """
            ),
            {"option_group": option_group, "option_key": option_key, "label": label},
        )


def downgrade() -> None:
    op.drop_index("ix_silver_manual_investment_positions_product_id", table_name="manual_investment_positions", schema="silver")
    op.drop_column("manual_investment_positions", "liquidity_type", schema="silver")
    op.drop_column("manual_investment_positions", "rate_periodicity", schema="silver")
    op.drop_column("manual_investment_positions", "rate_spread", schema="silver")
    op.drop_column("manual_investment_positions", "rate_percent", schema="silver")
    op.drop_column("manual_investment_positions", "rate_index", schema="silver")
    op.drop_column("manual_investment_positions", "rate_type", schema="silver")
    op.drop_column("manual_investment_positions", "product_id", schema="silver")

    op.drop_index("ix_silver_cards_brand_id", table_name="cards", schema="silver")
    op.drop_index("ix_silver_cards_institution_id", table_name="cards", schema="silver")
    op.drop_column("cards", "is_virtual", schema="silver")
    op.drop_column("cards", "brand_id", schema="silver")
    op.drop_column("cards", "institution_id", schema="silver")

    op.drop_index("ix_app_reference_options_group_active", table_name="reference_options", schema="app")
    op.drop_constraint("uq_app_institutions_name", "institutions", schema="app", type_="unique")
    op.drop_table("reference_options", schema="app")
