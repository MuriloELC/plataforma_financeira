"""create initial data model

Revision ID: 20260625_0002
Revises: 20260625_0001
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260625_0002"
down_revision: Union[str, Sequence[str], None] = "20260625_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB
MONEY = sa.Numeric(14, 2)
QUANTITY = sa.Numeric(20, 8)
RATE = sa.Numeric(14, 6)
CONFIDENCE = sa.Numeric(5, 4)


def uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        UUID,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def updated_at() -> sa.Column:
    return sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def source_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column("source_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=True),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=True),
        sa.Column("raw_reference", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("confidence_score", CONFIDENCE, nullable=False, server_default="1.0000"),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("review_status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
    )


def create_app_tables() -> None:
    op.create_table(
        "institutions",
        uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("institution_type", sa.Text(), nullable=False, server_default=sa.text("'other'")),
        sa.Column("country", sa.Text(), nullable=False, server_default=sa.text("'BR'")),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        created_at(),
        schema="app",
    )
    op.create_index("ix_app_institutions_name", "institutions", ["name"], schema="app")

    op.create_table(
        "categories",
        uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("app.categories.id"), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        created_at(),
        sa.UniqueConstraint("name", "type", name="uq_app_categories_name_type"),
        schema="app",
    )
    op.create_index("ix_app_categories_parent_id", "categories", ["parent_id"], schema="app")

    op.create_table(
        "accounts",
        uuid_pk(),
        sa.Column("institution_id", UUID, sa.ForeignKey("app.institutions.id"), nullable=True),
        sa.Column("institution", sa.Text(), nullable=False),
        sa.Column("account_name", sa.Text(), nullable=False),
        sa.Column("account_type", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default=sa.text("'BRL'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        created_at(),
        schema="app",
    )
    op.create_index("ix_app_accounts_institution_id", "accounts", ["institution_id"], schema="app")

    op.create_table(
        "settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", JSONB, nullable=False),
        updated_at(),
        schema="app",
    )

    op.create_table(
        "goals",
        uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("goal_type", sa.Text(), nullable=False),
        sa.Column("target_amount", MONEY, nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("current_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        created_at(),
        updated_at(),
        schema="app",
    )
    op.create_index("ix_app_goals_goal_type", "goals", ["goal_type"], schema="app")

    op.create_table(
        "purchase_decisions",
        uuid_pk(),
        sa.Column("decision_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("item_name", sa.Text(), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("category_id", UUID, sa.ForeignKey("app.categories.id"), nullable=True),
        sa.Column("is_planned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_technology", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payment_method", sa.Text(), nullable=False),
        sa.Column("installments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("monthly_installment", MONEY, nullable=True),
        sa.Column("urgency", sa.Text(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column("reserve_impact_amount", MONEY, nullable=True),
        sa.Column("contribution_impact_amount", MONEY, nullable=True),
        sa.Column("goal_100k_delay_days", sa.Integer(), nullable=True),
        sa.Column("future_commitment_impact", MONEY, nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        created_at(),
        schema="app",
    )
    op.create_index("ix_app_purchase_decisions_category_id", "purchase_decisions", ["category_id"], schema="app")
    op.create_index("ix_app_purchase_decisions_decision_date", "purchase_decisions", ["decision_date"], schema="app")

    op.create_table(
        "audit_logs",
        uuid_pk(),
        sa.Column("entity_schema", sa.Text(), nullable=False),
        sa.Column("entity_table", sa.Text(), nullable=False),
        sa.Column("entity_id", UUID, nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False, server_default=sa.text("'system'")),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("before_payload", JSONB, nullable=True),
        sa.Column("after_payload", JSONB, nullable=True),
        created_at(),
        schema="app",
    )
    op.create_index("ix_app_audit_logs_entity", "audit_logs", ["entity_schema", "entity_table", "entity_id"], schema="app")


def create_bronze_tables() -> None:
    op.create_table(
        "raw_files",
        uuid_pk(),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("file_extension", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=True),
        sa.Column("detected_institution", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'uploaded'")),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("sha256_hash", name="uq_bronze_raw_files_sha256_hash"),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_files_uploaded_at", "raw_files", ["uploaded_at"], schema="bronze")

    op.create_table(
        "import_batches",
        uuid_pk(),
        sa.Column("raw_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("parser_name", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        created_at(),
        schema="bronze",
    )
    op.create_index("ix_bronze_import_batches_raw_file_id", "import_batches", ["raw_file_id"], schema="bronze")
    op.create_index("ix_bronze_import_batches_status", "import_batches", ["status"], schema="bronze")

    op.create_table(
        "raw_file_metadata",
        uuid_pk(),
        sa.Column("raw_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=False),
        sa.Column("metadata_key", sa.Text(), nullable=False),
        sa.Column("metadata_value", JSONB, nullable=False),
        created_at(),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_file_metadata_raw_file_id", "raw_file_metadata", ["raw_file_id"], schema="bronze")

    op.create_table(
        "raw_csv_rows",
        uuid_pk(),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("raw_payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_csv_rows_import_batch_id", "raw_csv_rows", ["import_batch_id"], schema="bronze")

    op.create_table(
        "raw_sheet_data",
        uuid_pk(),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=False),
        sa.Column("sheet_name", sa.Text(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("raw_payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_sheet_data_import_batch_id", "raw_sheet_data", ["import_batch_id"], schema="bronze")

    op.create_table(
        "raw_xlsx_rows",
        uuid_pk(),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=False),
        sa.Column("sheet_name", sa.Text(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_xlsx_rows_import_batch_id", "raw_xlsx_rows", ["import_batch_id"], schema="bronze")

    op.create_table(
        "raw_pdf_text",
        uuid_pk(),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extraction_metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_pdf_text_import_batch_id", "raw_pdf_text", ["import_batch_id"], schema="bronze")

    op.create_table(
        "raw_pdf_pages",
        uuid_pk(),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extraction_metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="bronze",
    )
    op.create_index("ix_bronze_raw_pdf_pages_import_batch_id", "raw_pdf_pages", ["import_batch_id"], schema="bronze")

    op.create_table(
        "parser_errors",
        uuid_pk(),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=False),
        sa.Column("raw_reference", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_type", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        created_at(),
        schema="bronze",
    )
    op.create_index("ix_bronze_parser_errors_import_batch_id", "parser_errors", ["import_batch_id"], schema="bronze")


def create_silver_tables() -> None:
    op.create_table(
        "accounts",
        uuid_pk(),
        sa.Column("institution_id", UUID, sa.ForeignKey("app.institutions.id"), nullable=True),
        sa.Column("institution", sa.Text(), nullable=False),
        sa.Column("account_name", sa.Text(), nullable=False),
        sa.Column("account_type", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default=sa.text("'BRL'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_accounts_institution_id", "accounts", ["institution_id"], schema="silver")

    op.create_table(
        "cash_transactions",
        uuid_pk(),
        sa.Column("account_id", UUID, sa.ForeignKey("silver.accounts.id"), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("posted_date", sa.Date(), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("description_clean", sa.Text(), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("category_id", UUID, sa.ForeignKey("app.categories.id"), nullable=True),
        sa.Column("transaction_type", sa.Text(), nullable=False, server_default=sa.text("'cash'")),
        sa.Column("is_transfer", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()),
        *source_columns(),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_cash_transactions_account_id", "cash_transactions", ["account_id"], schema="silver")
    op.create_index("ix_silver_cash_transactions_category_id", "cash_transactions", ["category_id"], schema="silver")
    op.create_index("ix_silver_cash_transactions_transaction_date", "cash_transactions", ["transaction_date"], schema="silver")

    op.create_table(
        "cards",
        uuid_pk(),
        sa.Column("institution", sa.Text(), nullable=False),
        sa.Column("card_name", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("last_four_digits", sa.Text(), nullable=True),
        sa.Column("credit_limit", MONEY, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        created_at(),
        schema="silver",
    )

    op.create_table(
        "card_invoices",
        uuid_pk(),
        sa.Column("card_id", UUID, sa.ForeignKey("silver.cards.id"), nullable=False),
        sa.Column("reference_month", sa.Date(), nullable=False),
        sa.Column("closing_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("total_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("minimum_payment", MONEY, nullable=True),
        sa.Column("credit_limit", MONEY, nullable=True),
        sa.Column("used_limit", MONEY, nullable=True),
        sa.Column("available_limit", MONEY, nullable=True),
        sa.Column("next_invoice_committed_amount", MONEY, nullable=True),
        sa.Column("future_debt_total", MONEY, nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'open'")),
        sa.Column("source_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=True),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=True),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_card_invoices_card_id", "card_invoices", ["card_id"], schema="silver")
    op.create_index("ix_silver_card_invoices_reference_month", "card_invoices", ["reference_month"], schema="silver")

    op.create_table(
        "card_transactions",
        uuid_pk(),
        sa.Column("invoice_id", UUID, sa.ForeignKey("silver.card_invoices.id"), nullable=True),
        sa.Column("card_id", UUID, sa.ForeignKey("silver.cards.id"), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("description_clean", sa.Text(), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("category_id", UUID, sa.ForeignKey("app.categories.id"), nullable=True),
        sa.Column("installment_number", sa.Integer(), nullable=True),
        sa.Column("installment_total", sa.Integer(), nullable=True),
        sa.Column("is_installment", sa.Boolean(), nullable=False, server_default=sa.false()),
        *source_columns(),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_card_transactions_card_id", "card_transactions", ["card_id"], schema="silver")
    op.create_index("ix_silver_card_transactions_invoice_id", "card_transactions", ["invoice_id"], schema="silver")
    op.create_index("ix_silver_card_transactions_purchase_date", "card_transactions", ["purchase_date"], schema="silver")

    op.create_table(
        "installments",
        uuid_pk(),
        sa.Column("card_transaction_id", UUID, sa.ForeignKey("silver.card_transactions.id"), nullable=False),
        sa.Column("installment_number", sa.Integer(), nullable=False),
        sa.Column("installment_total", sa.Integer(), nullable=False),
        sa.Column("installment_amount", MONEY, nullable=False),
        sa.Column("due_month", sa.Date(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_installments_card_transaction_id", "installments", ["card_transaction_id"], schema="silver")
    op.create_index("ix_silver_installments_due_month", "installments", ["due_month"], schema="silver")

    op.create_table(
        "investment_assets",
        uuid_pk(),
        sa.Column("asset_code", sa.Text(), nullable=False),
        sa.Column("asset_name", sa.Text(), nullable=False),
        sa.Column("asset_class", sa.Text(), nullable=False),
        sa.Column("institution", sa.Text(), nullable=True),
        sa.Column("ticker", sa.Text(), nullable=True),
        sa.Column("cnpj", sa.Text(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=False, server_default=sa.text("'BRL'")),
        sa.Column("risk_level", sa.Text(), nullable=True),
        sa.Column("default_counts_as_reserve", sa.Boolean(), nullable=False, server_default=sa.false()),
        created_at(),
        sa.UniqueConstraint("asset_code", "institution", name="uq_silver_investment_assets_code_institution"),
        schema="silver",
    )
    op.create_index("ix_silver_investment_assets_asset_class", "investment_assets", ["asset_class"], schema="silver")

    op.create_table(
        "investment_positions",
        uuid_pk(),
        sa.Column("asset_id", UUID, sa.ForeignKey("silver.investment_assets.id"), nullable=False),
        sa.Column("institution", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("quantity", QUANTITY, nullable=True),
        sa.Column("gross_value", MONEY, nullable=True),
        sa.Column("net_value", MONEY, nullable=True),
        sa.Column("market_value", MONEY, nullable=True),
        sa.Column("liquidity", sa.Text(), nullable=True),
        sa.Column("maturity_date", sa.Date(), nullable=True),
        sa.Column("rate_description", sa.Text(), nullable=True),
        sa.Column("counts_as_reserve", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_manual", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=True),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_investment_positions_asset_id", "investment_positions", ["asset_id"], schema="silver")
    op.create_index("ix_silver_investment_positions_reference_date", "investment_positions", ["reference_date"], schema="silver")

    op.create_table(
        "manual_investment_positions",
        uuid_pk(),
        sa.Column("asset_id", UUID, sa.ForeignKey("silver.investment_assets.id"), nullable=True),
        sa.Column("institution", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("asset_class", sa.Text(), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("gross_value", MONEY, nullable=False),
        sa.Column("net_value", MONEY, nullable=True),
        sa.Column("liquidity", sa.Text(), nullable=True),
        sa.Column("maturity_date", sa.Date(), nullable=True),
        sa.Column("rate_description", sa.Text(), nullable=True),
        sa.Column("counts_as_reserve", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        created_at(),
        updated_at(),
        schema="silver",
    )
    op.create_index("ix_silver_manual_investment_positions_reference_date", "manual_investment_positions", ["reference_date"], schema="silver")

    for table_name in ("investment_trades", "investment_transactions"):
        op.create_table(
            table_name,
            uuid_pk(),
            sa.Column("asset_id", UUID, sa.ForeignKey("silver.investment_assets.id"), nullable=False),
            sa.Column("trade_date", sa.Date(), nullable=False),
            sa.Column("side", sa.Text(), nullable=False),
            sa.Column("quantity", QUANTITY, nullable=False),
            sa.Column("unit_price", RATE, nullable=True),
            sa.Column("gross_amount", MONEY, nullable=True),
            sa.Column("fees", MONEY, nullable=True),
            sa.Column("net_amount", MONEY, nullable=True),
            sa.Column("institution", sa.Text(), nullable=True),
            sa.Column("source_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=True),
            sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=True),
            created_at(),
            schema="silver",
        )
        op.create_index(f"ix_silver_{table_name}_asset_id", table_name, ["asset_id"], schema="silver")
        op.create_index(f"ix_silver_{table_name}_trade_date", table_name, ["trade_date"], schema="silver")

    op.create_table(
        "investment_income",
        uuid_pk(),
        sa.Column("asset_id", UUID, sa.ForeignKey("silver.investment_assets.id"), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("income_type", sa.Text(), nullable=False),
        sa.Column("gross_amount", MONEY, nullable=True),
        sa.Column("tax_amount", MONEY, nullable=True),
        sa.Column("net_amount", MONEY, nullable=True),
        sa.Column("is_received", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_accrued", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=True),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=True),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_investment_income_asset_id", "investment_income", ["asset_id"], schema="silver")
    op.create_index("ix_silver_investment_income_reference_date", "investment_income", ["reference_date"], schema="silver")

    op.create_table(
        "pension_positions",
        uuid_pk(),
        sa.Column("institution", sa.Text(), nullable=False),
        sa.Column("plan_name", sa.Text(), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("employee_contribution", MONEY, nullable=True),
        sa.Column("employer_contribution", MONEY, nullable=True),
        sa.Column("total_balance", MONEY, nullable=True),
        sa.Column("vested_balance", MONEY, nullable=True),
        sa.Column("vesting_rule", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_pension_positions_reference_date", "pension_positions", ["reference_date"], schema="silver")

    op.create_table(
        "payroll_statements",
        uuid_pk(),
        sa.Column("employer", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("competence_month", sa.Date(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("base_salary", MONEY, nullable=True),
        sa.Column("gross_income", MONEY, nullable=True),
        sa.Column("total_deductions", MONEY, nullable=True),
        sa.Column("net_income", MONEY, nullable=True),
        sa.Column("fgts_amount", MONEY, nullable=True),
        sa.Column("source_file_id", UUID, sa.ForeignKey("bronze.raw_files.id"), nullable=True),
        sa.Column("import_batch_id", UUID, sa.ForeignKey("bronze.import_batches.id"), nullable=True),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_payroll_statements_competence_month", "payroll_statements", ["competence_month"], schema="silver")

    for table_name, item_type in (("payroll_earnings", "earning"), ("payroll_deductions", "deduction")):
        op.create_table(
            table_name,
            uuid_pk(),
            sa.Column("payroll_statement_id", UUID, sa.ForeignKey("silver.payroll_statements.id"), nullable=False),
            sa.Column("item_code", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("reference", sa.Numeric(14, 4), nullable=True),
            sa.Column("amount", MONEY, nullable=False),
            sa.Column("classification", sa.Text(), nullable=True),
            sa.Column("item_type", sa.Text(), nullable=False, server_default=sa.text(f"'{item_type}'")),
            created_at(),
            schema="silver",
        )
        op.create_index(f"ix_silver_{table_name}_payroll_statement_id", table_name, ["payroll_statement_id"], schema="silver")

    op.create_table(
        "payroll_items",
        uuid_pk(),
        sa.Column("payroll_statement_id", UUID, sa.ForeignKey("silver.payroll_statements.id"), nullable=False),
        sa.Column("item_code", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("item_type", sa.Text(), nullable=False),
        sa.Column("reference", sa.Numeric(14, 4), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("classification", sa.Text(), nullable=True),
        created_at(),
        schema="silver",
    )
    op.create_index("ix_silver_payroll_items_payroll_statement_id", "payroll_items", ["payroll_statement_id"], schema="silver")

    op.create_table(
        "purchase_decisions",
        uuid_pk(),
        sa.Column("decision_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("item_name", sa.Text(), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("category_id", UUID, sa.ForeignKey("app.categories.id"), nullable=True),
        sa.Column("is_planned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_technology", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payment_method", sa.Text(), nullable=False),
        sa.Column("installments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("monthly_installment", MONEY, nullable=True),
        sa.Column("urgency", sa.Text(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column("reserve_impact_amount", MONEY, nullable=True),
        sa.Column("contribution_impact_amount", MONEY, nullable=True),
        sa.Column("goal_100k_delay_days", sa.Integer(), nullable=True),
        sa.Column("future_commitment_impact", MONEY, nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        created_at(),
        schema="silver",
    )


def create_gold_tables() -> None:
    op.create_table(
        "passive_income_monthly",
        uuid_pk(),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("received_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("accrued_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("avg_3m_received", MONEY, nullable=True),
        sa.Column("avg_12m_received", MONEY, nullable=True),
        sa.Column("target_amount", MONEY, nullable=False, server_default="5000"),
        sa.Column("progress_pct", sa.Numeric(8, 4), nullable=True),
        created_at(),
        sa.UniqueConstraint("month", name="uq_gold_passive_income_monthly_month"),
        schema="gold",
    )

    op.create_table(
        "goal_100k_progress",
        uuid_pk(),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("invested_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("target_amount", MONEY, nullable=False, server_default="100000"),
        sa.Column("remaining_amount", MONEY, nullable=True),
        sa.Column("progress_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("avg_monthly_contribution", MONEY, nullable=True),
        sa.Column("estimated_months_to_goal", sa.Integer(), nullable=True),
        created_at(),
        sa.UniqueConstraint("reference_date", name="uq_gold_goal_100k_progress_reference_date"),
        schema="gold",
    )

    op.create_table(
        "reserve_status",
        uuid_pk(),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("avg_monthly_expenses_3m", MONEY, nullable=False, server_default="0"),
        sa.Column("reserve_months", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("reserve_target", MONEY, nullable=False, server_default="0"),
        sa.Column("eligible_reserve_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("gap_amount", MONEY, nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        created_at(),
        sa.UniqueConstraint("reference_date", name="uq_gold_reserve_status_reference_date"),
        schema="gold",
    )

    op.create_table(
        "portfolio_allocation",
        uuid_pk(),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("asset_class", sa.Text(), nullable=False),
        sa.Column("amount", MONEY, nullable=False, server_default="0"),
        sa.Column("allocation_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("counts_as_reserve", sa.Boolean(), nullable=False, server_default=sa.false()),
        created_at(),
        schema="gold",
    )
    op.create_index("ix_gold_portfolio_allocation_reference_date", "portfolio_allocation", ["reference_date"], schema="gold")

    op.create_table(
        "future_commitments",
        uuid_pk(),
        sa.Column("due_month", sa.Date(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("commitment_type", sa.Text(), nullable=False),
        created_at(),
        schema="gold",
    )
    op.create_index("ix_gold_future_commitments_due_month", "future_commitments", ["due_month"], schema="gold")

    op.create_table(
        "purchase_decision_context",
        uuid_pk(),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("net_income", MONEY, nullable=True),
        sa.Column("minimum_monthly_contribution", MONEY, nullable=False, server_default="300"),
        sa.Column("reserve_target", MONEY, nullable=False, server_default="0"),
        sa.Column("eligible_reserve_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("invested_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("goal_100k_remaining", MONEY, nullable=True),
        sa.Column("future_commitments_next_month", MONEY, nullable=True),
        sa.Column("available_after_commitments", MONEY, nullable=True),
        created_at(),
        sa.UniqueConstraint("reference_date", name="uq_gold_purchase_decision_context_reference_date"),
        schema="gold",
    )

    op.create_table(
        "financial_alerts",
        uuid_pk(),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("alert_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'open'")),
        created_at(),
        schema="gold",
    )
    op.create_index("ix_gold_financial_alerts_reference_date", "financial_alerts", ["reference_date"], schema="gold")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    create_app_tables()
    create_bronze_tables()
    create_silver_tables()
    create_gold_tables()


def downgrade() -> None:
    tables = (
        ("gold", "financial_alerts"),
        ("gold", "purchase_decision_context"),
        ("gold", "future_commitments"),
        ("gold", "portfolio_allocation"),
        ("gold", "reserve_status"),
        ("gold", "goal_100k_progress"),
        ("gold", "passive_income_monthly"),
        ("silver", "purchase_decisions"),
        ("silver", "payroll_items"),
        ("silver", "payroll_deductions"),
        ("silver", "payroll_earnings"),
        ("silver", "payroll_statements"),
        ("silver", "pension_positions"),
        ("silver", "investment_income"),
        ("silver", "investment_transactions"),
        ("silver", "investment_trades"),
        ("silver", "manual_investment_positions"),
        ("silver", "investment_positions"),
        ("silver", "investment_assets"),
        ("silver", "installments"),
        ("silver", "card_transactions"),
        ("silver", "card_invoices"),
        ("silver", "cards"),
        ("silver", "cash_transactions"),
        ("silver", "accounts"),
        ("bronze", "parser_errors"),
        ("bronze", "raw_pdf_pages"),
        ("bronze", "raw_pdf_text"),
        ("bronze", "raw_xlsx_rows"),
        ("bronze", "raw_sheet_data"),
        ("bronze", "raw_csv_rows"),
        ("bronze", "raw_file_metadata"),
        ("bronze", "import_batches"),
        ("bronze", "raw_files"),
        ("app", "audit_logs"),
        ("app", "purchase_decisions"),
        ("app", "goals"),
        ("app", "settings"),
        ("app", "accounts"),
        ("app", "categories"),
        ("app", "institutions"),
    )
    for schema, table in tables:
        op.drop_table(table, schema=schema)
