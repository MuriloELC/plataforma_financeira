import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import create_database_engine
from app.main import create_app


TABLES = (
    "app.audit_logs",
    "app.goals",
    "app.categories",
    "silver.cash_transactions",
    "silver.manual_investment_positions",
    "silver.accounts",
    "silver.investment_assets",
)


@pytest.fixture(autouse=True)
def manual_test_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate manual CRUD with PostgreSQL.")

    monkeypatch.setenv("FILE_STORAGE_PATH", str(tmp_path / "storage"))
    get_settings.cache_clear()

    engine = create_database_engine()
    with engine.begin() as connection:
        connection.execute(text(f"truncate table {', '.join(TABLES)} restart identity cascade"))

    yield

    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def scalar(sql: str, params: dict[str, Any] | None = None) -> Any:
    engine = create_database_engine()
    with engine.connect() as connection:
        return connection.execute(text(sql), params or {}).scalar_one()


def test_categories_crud_writes_audit_logs(client: TestClient) -> None:
    created = client.post("/categories", json={"name": "Tecnologia", "type": "expense"})
    assert created.status_code == 201, created.text
    category_id = created.json()["id"]

    listed = client.get("/categories")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Tecnologia"

    updated = client.patch(f"/categories/{category_id}", json={"name": "Tecnologia e Software"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Tecnologia e Software"

    deleted = client.delete(f"/categories/{category_id}")
    assert deleted.status_code == 204
    assert scalar(
        "select count(*) from app.audit_logs where entity_table = 'categories'"
    ) == 3


def test_accounts_and_manual_transactions_crud(client: TestClient) -> None:
    account = client.post(
        "/manual/accounts",
        json={
            "institution": "Banco Teste",
            "account_name": "Conta Manual",
            "account_type": "checking",
        },
    )
    assert account.status_code == 201, account.text
    account_id = account.json()["id"]

    category = client.post("/categories", json={"name": "Mercado", "type": "expense"})
    assert category.status_code == 201
    category_id = category.json()["id"]

    transaction = client.post(
        "/manual/transactions",
        json={
            "account_id": account_id,
            "transaction_date": "2026-06-10",
            "description_raw": "Compra manual",
            "amount": "-50.25",
            "category_id": category_id,
            "notes": "fixture anonima",
        },
    )
    assert transaction.status_code == 201, transaction.text
    transaction_id = transaction.json()["id"]
    assert transaction.json()["direction"] == "outflow"

    updated = client.patch(
        f"/manual/transactions/{transaction_id}",
        json={"amount": "100.00", "description_raw": "Ajuste manual"},
    )
    assert updated.status_code == 200
    assert updated.json()["direction"] == "inflow"

    listed = client.get("/manual/transactions")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted_transaction = client.delete(f"/manual/transactions/{transaction_id}")
    assert deleted_transaction.status_code == 204
    deleted_account = client.delete(f"/manual/accounts/{account_id}")
    assert deleted_account.status_code == 204

    assert scalar(
        "select count(*) from app.audit_logs where entity_table in ('accounts', 'cash_transactions')"
    ) == 5


def test_goals_crud_writes_audit_logs(client: TestClient) -> None:
    goal = client.post(
        "/manual/goals",
        json={
            "name": "R$ 100 mil investidos",
            "goal_type": "investment",
            "target_amount": "100000.00",
            "metadata": {"source": "manual_test"},
        },
    )
    assert goal.status_code == 201, goal.text
    goal_id = goal.json()["id"]

    updated = client.patch(
        f"/manual/goals/{goal_id}",
        json={"current_amount": "12000.00", "status": "active"},
    )
    assert updated.status_code == 200
    assert updated.json()["current_amount"] == "12000.00"

    listed = client.get("/manual/goals")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = client.delete(f"/manual/goals/{goal_id}")
    assert deleted.status_code == 204
    assert scalar("select count(*) from app.audit_logs where entity_table = 'goals'") == 3


def test_manual_investments_crud_preserves_reserve_flag(client: TestClient) -> None:
    cdb = client.post(
        "/manual/investments",
        json={
            "institution": "Mercado Livre",
            "product_name": "CDB Mercado Livre",
            "asset_class": "cdb",
            "reference_date": "2026-06-30",
            "gross_value": "4052.64",
            "net_value": "4052.64",
            "liquidity": "same_day",
            "maturity_date": "2028-06-12",
            "rate_description": "102% do CDI",
            "counts_as_reserve": True,
        },
    )
    assert cdb.status_code == 201, cdb.text
    cdb_id = cdb.json()["id"]

    pension = client.post(
        "/manual/investments",
        json={
            "institution": "Sicoob Previ",
            "product_name": "Sicoob Previ",
            "asset_class": "pension",
            "reference_date": "2026-06-30",
            "gross_value": "1000.00",
            "net_value": "1000.00",
            "liquidity": "illiquid",
            "counts_as_reserve": False,
        },
    )
    assert pension.status_code == 201, pension.text

    updated = client.patch(f"/manual/investments/{cdb_id}", json={"gross_value": "4100.00"})
    assert updated.status_code == 200
    assert updated.json()["gross_value"] == "4100.00"

    listed = client.get("/manual/investments")
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    assert scalar("select count(*) from silver.manual_investment_positions") == 2
    assert scalar(
        "select count(*) from silver.manual_investment_positions where counts_as_reserve = true"
    ) == 1

    deleted = client.delete(f"/manual/investments/{pension.json()['id']}")
    assert deleted.status_code == 204
    assert scalar(
        "select count(*) from app.audit_logs where entity_table = 'manual_investment_positions'"
    ) == 4
