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
    "app.reference_options",
    "app.institutions",
    "app.categorization_rules",
    "app.goals",
    "app.categories",
    "silver.installments",
    "silver.card_transactions",
    "silver.card_invoices",
    "silver.cards",
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
    assert any(item["name"] == "Tecnologia" for item in listed.json())

    updated = client.patch(f"/categories/{category_id}", json={"name": "Tecnologia e Software"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Tecnologia e Software"

    deleted = client.delete(f"/categories/{category_id}")
    assert deleted.status_code == 204
    assert scalar(
        "select count(*) from app.audit_logs where entity_table = 'categories'"
    ) == 3


def test_default_categories_and_categorization_rules_preview(client: TestClient) -> None:
    categories = client.get("/categories")
    assert categories.status_code == 200
    names = {item["name"] for item in categories.json()}
    assert {"Tecnologia", "Nao classificado", "Renda passiva"}.issubset(names)
    technology_id = next(item["id"] for item in categories.json() if item["name"] == "Tecnologia")

    rule = client.post(
        "/categorization-rules",
        json={
            "pattern": "notebook",
            "match_type": "contains",
            "category_id": technology_id,
            "priority": 1,
            "confidence_score": "0.9500",
        },
    )
    assert rule.status_code == 201, rule.text
    rule_id = rule.json()["id"]

    preview = client.post(
        "/categorize/preview",
        json={"description": "Compra notebook trabalho", "transaction_type": "cash"},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["category_name"] == "Tecnologia"
    assert preview.json()["matched_rule_id"] == rule_id
    assert preview.json()["needs_review"] is False

    updated = client.patch(f"/categorization-rules/{rule_id}", json={"confidence_score": "0.6000"})
    assert updated.status_code == 200
    low_confidence = client.post(
        "/categorize/preview",
        json={"description": "Compra notebook trabalho", "transaction_type": "cash"},
    )
    assert low_confidence.json()["needs_review"] is True

    unmatched = client.post("/categorize/preview", json={"description": "Descricao sem regra"})
    assert unmatched.status_code == 200
    assert unmatched.json()["category_name"] == "Nao classificado"
    assert unmatched.json()["needs_review"] is True

    deleted = client.delete(f"/categorization-rules/{rule_id}")
    assert deleted.status_code == 204
    assert scalar(
        "select count(*) from app.audit_logs where entity_table = 'categorization_rules'"
    ) == 3


def test_configuration_registries_can_create_edit_and_inactivate(client: TestClient) -> None:
    institutions = client.get("/config/institutions")
    assert institutions.status_code == 200
    assert any(item["name"] == "Sicoob" for item in institutions.json())

    created_institution = client.post(
        "/config/institutions",
        json={"name": "Banco Config", "institution_type": "bank"},
    )
    assert created_institution.status_code == 201, created_institution.text
    institution_id = created_institution.json()["id"]

    updated_institution = client.patch(
        f"/config/institutions/{institution_id}",
        json={"name": "Banco Config Editado", "is_active": False},
    )
    assert updated_institution.status_code == 200
    assert updated_institution.json()["name"] == "Banco Config Editado"
    assert updated_institution.json()["is_active"] is False

    option = client.post(
        "/config/options",
        json={
            "option_group": "investment_product",
            "option_key": "cdb_teste",
            "label": "CDB Teste",
        },
    )
    assert option.status_code == 201, option.text
    option_id = option.json()["id"]

    updated_option = client.patch(
        f"/config/options/{option_id}",
        json={"label": "CDB Teste Editado", "is_active": False},
    )
    assert updated_option.status_code == 200
    assert updated_option.json()["label"] == "CDB Teste Editado"
    assert updated_option.json()["is_active"] is False

    inactive_options = client.get("/config/options", params={"include_inactive": True})
    assert inactive_options.status_code == 200
    assert any(item["id"] == option_id for item in inactive_options.json())

    assert scalar(
        "select count(*) from app.audit_logs where entity_table in ('institutions', 'reference_options')"
    ) == 4


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
    product = client.post(
        "/config/options",
        json={
            "option_group": "investment_product",
            "option_key": "cdb_ml",
            "label": "CDB Mercado Livre",
        },
    )
    assert product.status_code == 201, product.text
    product_id = product.json()["id"]

    cdb = client.post(
        "/manual/investments",
        json={
            "institution": "Mercado Livre",
            "product_name": "CDB Mercado Livre",
            "product_id": product_id,
            "asset_class": "cdb",
            "reference_date": "2026-06-30",
            "gross_value": "4052.64",
            "net_value": "4052.64",
            "liquidity": "same_day",
            "liquidity_type": "daily",
            "maturity_date": "2028-06-12",
            "rate_description": "102% do CDI",
            "rate_type": "post_fixed",
            "rate_index": "cdi",
            "rate_percent": "102.0000",
            "rate_periodicity": "annual",
            "counts_as_reserve": True,
        },
    )
    assert cdb.status_code == 201, cdb.text
    cdb_id = cdb.json()["id"]
    assert cdb.json()["product_id"] == product_id
    assert cdb.json()["rate_type"] == "post_fixed"
    assert cdb.json()["liquidity_type"] == "daily"

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


def test_cards_invoices_and_installments_crud(client: TestClient) -> None:
    institution = client.post(
        "/config/institutions",
        json={"name": "Sicoob Teste", "institution_type": "bank"},
    )
    assert institution.status_code == 201, institution.text
    institution_id = institution.json()["id"]
    brand = client.post(
        "/config/options",
        json={"option_group": "card_brand", "option_key": "visa_teste", "label": "Visa Teste"},
    )
    assert brand.status_code == 201, brand.text
    brand_id = brand.json()["id"]

    card = client.post(
        "/cards",
        json={
            "institution": "Sicoob Teste",
            "institution_id": institution_id,
            "card_name": "Cartao Manual",
            "brand": "Visa Teste",
            "brand_id": brand_id,
            "last_four_digits": "1234",
            "credit_limit": "5000.00",
            "is_virtual": True,
        },
    )
    assert card.status_code == 201, card.text
    card_id = card.json()["id"]
    assert card.json()["institution_id"] == institution_id
    assert card.json()["brand_id"] == brand_id
    assert card.json()["is_virtual"] is True

    invoice = client.post(
        "/card-invoices",
        json={
            "card_id": card_id,
            "reference_month": "2026-06-01",
            "due_date": "2026-07-10",
            "total_amount": "300.00",
            "minimum_payment": "50.00",
            "status": "open",
        },
    )
    assert invoice.status_code == 201, invoice.text
    invoice_id = invoice.json()["id"]

    transaction = client.post(
        f"/card-invoices/{invoice_id}/transactions",
        json={
            "purchase_date": "2026-06-15",
            "description_raw": "Compra parcelada anonima",
            "amount": "100.00",
            "installment_number": 1,
            "installment_total": 3,
        },
    )
    assert transaction.status_code == 201, transaction.text
    assert transaction.json()["is_installment"] is True

    transactions = client.get("/card-transactions")
    assert transactions.status_code == 200
    assert len(transactions.json()) == 1
    assert transactions.json()[0]["card_name"] == "Cartao Manual"

    assert scalar("select count(*) from silver.installments") == 3
    assert scalar("select coalesce(sum(installment_amount), 0) from silver.installments") == 300

    updated = client.patch(f"/card-invoices/{invoice_id}", json={"status": "closed"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "closed"

    invoices = client.get("/card-invoices")
    assert invoices.status_code == 200
    assert len(invoices.json()) == 1

    deleted = client.delete(f"/card-invoices/{invoice_id}")
    assert deleted.status_code == 204
    assert scalar("select count(*) from silver.installments") == 0
    assert scalar(
        "select count(*) from app.audit_logs where entity_table in ('cards', 'card_invoices', 'card_transactions')"
    ) == 5
