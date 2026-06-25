import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import create_database_engine
from app.main import create_app


BRONZE_TABLES = (
    "bronze.parser_errors",
    "bronze.raw_pdf_pages",
    "bronze.raw_pdf_text",
    "bronze.raw_xlsx_rows",
    "bronze.raw_sheet_data",
    "bronze.raw_csv_rows",
    "bronze.raw_file_metadata",
    "bronze.import_batches",
    "bronze.raw_files",
)

SILVER_TABLES = (
    "silver.payroll_deductions",
    "silver.payroll_earnings",
    "silver.payroll_items",
    "silver.payroll_statements",
    "silver.installments",
    "silver.card_transactions",
    "silver.card_invoices",
    "silver.investment_income",
    "silver.investment_transactions",
    "silver.investment_trades",
    "silver.investment_positions",
    "silver.manual_investment_positions",
    "silver.cash_transactions",
    "silver.cards",
    "silver.accounts",
    "silver.investment_assets",
)


@pytest.fixture(autouse=True)
def silver_test_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate Silver normalization with PostgreSQL.")

    monkeypatch.setenv("FILE_STORAGE_PATH", str(tmp_path / "storage"))
    get_settings.cache_clear()

    engine = create_database_engine()
    tables = ", ".join((*BRONZE_TABLES, *SILVER_TABLES))
    with engine.begin() as connection:
        connection.execute(text(f"truncate table {tables} restart identity cascade"))

    yield

    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def fixture_path(relative_path: str) -> Path:
    return Path(os.getenv("FIXTURES_PATH", "fixtures")) / relative_path


def upload_fixture(client: TestClient, relative_path: str, content_type: str) -> dict[str, Any]:
    path = fixture_path(relative_path)
    with path.open("rb") as file_handle:
        response = client.post(
            "/files/upload",
            files={"file": (path.name, file_handle, content_type)},
        )
    assert response.status_code == 201, response.text
    return response.json()


def approve_fixture(client: TestClient, relative_path: str, content_type: str) -> dict[str, Any]:
    upload = upload_fixture(client, relative_path, content_type)
    batch_id = upload["import_batch"]["id"]

    preview = client.get(f"/import-batches/{batch_id}/preview")
    assert preview.status_code == 200, preview.text
    assert preview.json()["import_batch_id"] == batch_id

    response = client.post(f"/import-batches/{batch_id}/approve")
    assert response.status_code == 200, response.text
    return response.json()


def scalar(sql: str, params: dict[str, Any] | None = None) -> Any:
    engine = create_database_engine()
    with engine.connect() as connection:
        return connection.execute(text(sql), params or {}).scalar_one()


def rows(sql: str, params: dict[str, Any] | None = None) -> list[Any]:
    engine = create_database_engine()
    with engine.connect() as connection:
        return connection.execute(text(sql), params or {}).mappings().all()


def test_approve_mercado_livre_statement_creates_cash_transactions_idempotently(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/mercado_livre/account_statement_sample.csv",
        "text/csv",
    )
    batch_id = approved["import_batch_id"]

    assert approved["status"] == "approved_to_silver"
    assert approved["silver_counts"]["cash_transactions"] == 17

    second = client.post(f"/import-batches/{batch_id}/approve")
    assert second.status_code == 200
    assert second.json()["silver_counts"]["cash_transactions"] == 17

    assert scalar(
        "select count(*) from silver.cash_transactions where import_batch_id = :batch_id",
        {"batch_id": batch_id},
    ) == 17


def test_approve_sicoob_checking_marks_card_payment_and_own_transfer(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/sicoob/extrato_conta_sample.pdf",
        "application/pdf",
    )
    batch_id = approved["import_batch_id"]

    card_payment = rows(
        """
        select transaction_type, is_transfer, amount
        from silver.cash_transactions
        where import_batch_id = :batch_id
          and transaction_type = 'card_payment'
        """,
        {"batch_id": batch_id},
    )
    own_transfer = rows(
        """
        select transaction_type, is_transfer, amount
        from silver.cash_transactions
        where import_batch_id = :batch_id
          and transaction_type = 'investment_transfer'
        """,
        {"batch_id": batch_id},
    )

    assert len(card_payment) == 1
    assert card_payment[0]["is_transfer"] is False
    assert str(card_payment[0]["amount"]) == "-1779.79"
    assert len(own_transfer) == 1
    assert own_transfer[0]["is_transfer"] is True


def test_approve_b3_monthly_creates_positions_income_and_trades(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/b3/relatorio-consolidado-mensal-sample.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    batch_id = approved["import_batch_id"]

    assert approved["silver_counts"]["investment_positions"] == 6
    assert approved["silver_counts"]["investment_income"] == 3
    assert approved["silver_counts"]["investment_trades"] == 3
    assert scalar(
        """
        select count(*)
        from silver.investment_positions p
        join silver.investment_assets a on a.id = p.asset_id
        where p.import_batch_id = :batch_id
          and a.asset_class = 'renda_fixa'
          and p.counts_as_reserve = false
        """,
        {"batch_id": batch_id},
    ) == 2


def test_approve_card_invoice_creates_transactions_and_future_installments(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/sicoob/fatura_cartao_sample.pdf",
        "application/pdf",
    )
    batch_id = approved["import_batch_id"]

    assert approved["silver_counts"]["card_invoices"] == 1
    assert approved["silver_counts"]["card_transactions"] == 10
    assert approved["silver_counts"]["installments"] > 10

    second = client.post(f"/import-batches/{batch_id}/approve")
    assert second.status_code == 200
    assert scalar(
        "select count(*) from silver.card_transactions where import_batch_id = :batch_id",
        {"batch_id": batch_id},
    ) == 10
    assert scalar(
        """
        select count(*)
        from silver.installments i
        join silver.card_transactions t on t.id = i.card_transaction_id
        where t.import_batch_id = :batch_id
          and i.due_month > date '2026-06-01'
        """,
        {"batch_id": batch_id},
    ) > 0


def test_approve_payroll_creates_statement_earnings_and_deductions(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/sicoob/contracheque_sample.pdf",
        "application/pdf",
    )
    batch_id = approved["import_batch_id"]

    assert approved["silver_counts"]["payroll_statements"] == 1
    assert approved["silver_counts"]["payroll_earnings"] == 4
    assert approved["silver_counts"]["payroll_deductions"] == 4
    assert str(
        scalar(
            "select fgts_amount from silver.payroll_statements where import_batch_id = :batch_id",
            {"batch_id": batch_id},
        )
    ) == "278.20"


def test_approve_sicoob_investments_preserves_reserve_eligibility(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/sicoob/investimentos_sicoob_sample.pdf",
        "application/pdf",
    )
    batch_id = approved["import_batch_id"]

    assert approved["silver_counts"]["investment_positions"] == 2
    reserve_flags = rows(
        """
        select a.asset_name, p.counts_as_reserve
        from silver.investment_positions p
        join silver.investment_assets a on a.id = p.asset_id
        where p.import_batch_id = :batch_id
        order by a.asset_name
        """,
        {"batch_id": batch_id},
    )

    assert [row["counts_as_reserve"] for row in reserve_flags] == [False, True]


def test_approve_manual_cdb_creates_manual_investment_position(client: TestClient) -> None:
    approved = approve_fixture(
        client,
        "anonymized/mercado_livre/cdb_position_sample.csv",
        "text/csv",
    )

    assert approved["silver_counts"]["manual_investment_positions"] == 1
    assert scalar("select count(*) from silver.manual_investment_positions where counts_as_reserve = true") == 1
