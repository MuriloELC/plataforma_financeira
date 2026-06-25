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

GOLD_TABLES = (
    "gold.passive_income_monthly",
    "gold.goal_100k_progress",
    "gold.reserve_status",
    "gold.portfolio_allocation",
    "gold.future_commitments",
    "gold.purchase_decision_context",
    "gold.financial_alerts",
)


@pytest.fixture(autouse=True)
def bronze_test_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate Bronze ingestion with PostgreSQL.")

    monkeypatch.setenv("FILE_STORAGE_PATH", str(tmp_path / "storage"))
    get_settings.cache_clear()

    engine = create_database_engine()
    tables = ", ".join(BRONZE_TABLES)
    with engine.begin() as connection:
        connection.execute(text(f"truncate table {tables} restart identity cascade"))

    yield

    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def fixture_path(relative_path: str) -> Path:
    root = Path(os.getenv("FIXTURES_PATH", "fixtures"))
    return root / relative_path


def upload_fixture(client: TestClient, relative_path: str, content_type: str) -> dict[str, Any]:
    path = fixture_path(relative_path)
    with path.open("rb") as file_handle:
        response = client.post(
            "/files/upload",
            files={"file": (path.name, file_handle, content_type)},
        )

    assert response.status_code == 201, response.text
    return response.json()


def scalar_count(sql: str, params: dict[str, Any] | None = None) -> int:
    engine = create_database_engine()
    with engine.connect() as connection:
        return int(connection.execute(text(sql), params or {}).scalar_one())


def table_counts(tables: tuple[str, ...]) -> dict[str, int]:
    return {table: scalar_count(f"select count(*) from {table}") for table in tables}


def test_upload_csv_registers_raw_file_batch_and_rows(client: TestClient) -> None:
    gold_counts_before = table_counts(GOLD_TABLES)

    body = upload_fixture(
        client,
        "anonymized/mercado_livre/account_statement_sample.csv",
        "text/csv",
    )

    assert body["duplicate"] is False
    assert body["raw_file"]["sha256_hash"]
    assert body["raw_file"]["status"] == "raw_extracted"
    assert body["raw_file"]["source_type"] == "mercado_livre_account_statement_csv"
    assert body["import_batch"]["status"] == "raw_extracted"
    assert body["import_batch"]["total_records"] > 0
    assert body["raw_counts"]["csv_rows"] == body["import_batch"]["total_records"]

    files_response = client.get("/files")
    assert files_response.status_code == 200
    assert files_response.json()[0]["id"] == body["raw_file"]["id"]

    batch_response = client.get(f"/import-batches/{body['import_batch']['id']}")
    assert batch_response.status_code == 200
    assert batch_response.json()["raw_counts"]["csv_rows"] == body["raw_counts"]["csv_rows"]
    assert table_counts(GOLD_TABLES) == gold_counts_before


def test_duplicate_upload_reuses_raw_file_and_creates_duplicate_batch(client: TestClient) -> None:
    first = upload_fixture(
        client,
        "anonymized/mercado_livre/account_statement_sample.csv",
        "text/csv",
    )
    second = upload_fixture(
        client,
        "anonymized/mercado_livre/account_statement_sample.csv",
        "text/csv",
    )

    assert second["duplicate"] is True
    assert second["raw_file"]["id"] == first["raw_file"]["id"]
    assert second["import_batch"]["status"] == "duplicate"
    assert second["raw_counts"]["csv_rows"] == 0
    assert scalar_count("select count(*) from bronze.raw_files") == 1
    assert scalar_count("select count(*) from bronze.import_batches") == 2


@pytest.mark.parametrize(
    ("relative_path", "content_type", "source_type", "count_field"),
    (
        (
            "anonymized/mercado_livre/cdb_position_sample.csv",
            "text/csv",
            "mercado_livre_manual_cdb_csv",
            "csv_rows",
        ),
        (
            "anonymized/b3/relatorio-consolidado-mensal-sample.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "b3_monthly_consolidated_xlsx",
            "xlsx_rows",
        ),
        (
            "anonymized/b3/relatorio-consolidado-anual-sample.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "b3_annual_consolidated_xlsx",
            "xlsx_rows",
        ),
        (
            "anonymized/sicoob/contracheque_sample.pdf",
            "application/pdf",
            "sicoob_payroll_pdf",
            "pdf_pages",
        ),
        (
            "anonymized/sicoob/extrato_conta_sample.pdf",
            "application/pdf",
            "sicoob_checking_statement_pdf",
            "pdf_pages",
        ),
        (
            "anonymized/sicoob/fatura_cartao_sample.pdf",
            "application/pdf",
            "sicoob_card_invoice_pdf",
            "pdf_pages",
        ),
        (
            "anonymized/sicoob/investimentos_sicoob_sample.pdf",
            "application/pdf",
            "sicoob_investments_pdf",
            "pdf_pages",
        ),
    ),
)
def test_upload_extracts_xlsx_and_pdf_raw_content(
    client: TestClient,
    relative_path: str,
    content_type: str,
    source_type: str,
    count_field: str,
) -> None:
    body = upload_fixture(client, relative_path, content_type)

    assert body["duplicate"] is False
    assert body["raw_file"]["source_type"] == source_type
    assert body["import_batch"]["status"] == "raw_extracted"
    assert body["raw_counts"][count_field] > 0
    assert body["raw_counts"]["parser_errors"] == 0


def test_upload_unsupported_extension_returns_400(client: TestClient) -> None:
    response = client.post(
        "/files/upload",
        files={"file": ("notes.txt", b"not a financial fixture", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_empty_file_returns_422(client: TestClient) -> None:
    response = client.post(
        "/files/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Uploaded file is empty."


def test_upload_rejects_file_above_configured_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_SIZE_BYTES", "10")
    get_settings.cache_clear()

    response = client.post(
        "/files/upload",
        files={"file": ("large.csv", b"01234567890", "text/csv")},
    )

    assert response.status_code == 413
    assert "configured limit" in response.json()["detail"]


def test_upload_response_masks_sensitive_filename_and_storage_path(client: TestClient) -> None:
    response = client.post(
        "/files/upload",
        files={"file": ("extrato_123.456.789-09.csv", b"linha;valor\n1;2\n", "text/csv")},
    )

    assert response.status_code == 201, response.text
    raw_file = response.json()["raw_file"]
    assert "123.456.789-09" not in raw_file["original_filename"]
    assert "***.***.***-**" in raw_file["original_filename"]
    assert "/" not in raw_file["stored_path"]
    assert "\\" not in raw_file["stored_path"]
