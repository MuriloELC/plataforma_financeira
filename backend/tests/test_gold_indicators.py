import os
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import create_database_engine
from app.main import create_app


TABLES = (
    "gold.financial_alerts",
    "gold.purchase_decision_context",
    "gold.future_commitments",
    "gold.portfolio_allocation",
    "gold.reserve_status",
    "gold.goal_100k_progress",
    "gold.passive_income_monthly",
    "silver.installments",
    "silver.card_transactions",
    "silver.card_invoices",
    "silver.cards",
    "silver.cash_transactions",
    "silver.investment_income",
    "silver.investment_positions",
    "silver.manual_investment_positions",
    "silver.accounts",
    "silver.investment_assets",
)


@pytest.fixture(autouse=True)
def gold_test_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate Gold indicators with PostgreSQL.")

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


def d(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def seed_silver(include_contribution: bool = True) -> None:
    engine = create_database_engine()
    with engine.begin() as connection:
        account_id = connection.execute(
            text(
                """
                insert into silver.accounts (institution, account_name, account_type)
                values ('Banco Teste', 'Conta Corrente', 'checking')
                returning id
                """
            )
        ).scalar_one()
        action_asset_id = _asset(connection, "BBSE3", "BBSE3", "acao", "B3", False)
        fixed_asset_id = _asset(connection, "CDBB3", "CDB B3", "renda_fixa", "B3", False)
        cdb_asset_id = _asset(connection, "CDBMANUAL", "CDB Manual", "cdb", "Manual", True)
        pension_asset_id = _asset(connection, "PREVI", "Sicoob Previ", "pension", "Sicoob Previ", False)

        connection.execute(
            text(
                """
                insert into silver.investment_positions (
                    asset_id, institution, source_type, reference_date, gross_value, market_value,
                    counts_as_reserve
                )
                values
                    (:action_asset_id, 'B3', 'b3_monthly_consolidated_xlsx', date '2026-06-30', 8000.00, 8000.00, false),
                    (:fixed_asset_id, 'B3', 'b3_monthly_consolidated_xlsx', date '2026-06-30', 2000.00, 2000.00, false)
                """
            ),
            {"action_asset_id": action_asset_id, "fixed_asset_id": fixed_asset_id},
        )
        connection.execute(
            text(
                """
                insert into silver.manual_investment_positions (
                    asset_id, institution, product_name, asset_class, reference_date, gross_value,
                    net_value, liquidity, counts_as_reserve
                )
                values
                    (:cdb_asset_id, 'Manual', 'CDB Manual', 'cdb', date '2026-06-30', 6000.00, 6000.00, 'same_day', true),
                    (:pension_asset_id, 'Sicoob Previ', 'Sicoob Previ', 'pension', date '2026-06-30', 10000.00, 10000.00, 'illiquid', false)
                """
            ),
            {"cdb_asset_id": cdb_asset_id, "pension_asset_id": pension_asset_id},
        )
        connection.execute(
            text(
                """
                insert into silver.investment_income (
                    asset_id, payment_date, reference_date, income_type, net_amount, source_type
                )
                values
                    (:asset_id, date '2026-04-20', date '2026-04-20', 'dividend', 100.00, 'test'),
                    (:asset_id, date '2026-05-20', date '2026-05-20', 'dividend', 200.00, 'test'),
                    (:asset_id, date '2026-06-20', date '2026-06-20', 'dividend', 300.00, 'test')
                """
            ),
            {"asset_id": action_asset_id},
        )
        cash_rows = [
            ("2026-04-10", "Despesa abril", "-1000.00", "cash", False),
            ("2026-05-10", "Despesa maio", "-1100.00", "cash", False),
            ("2026-06-10", "Despesa junho", "-900.00", "cash", False),
            ("2026-06-11", "Pagamento fatura", "-500.00", "card_payment", False),
        ]
        if include_contribution:
            cash_rows.append(("2026-06-12", "Aporte investimento", "-300.00", "investment_transfer", True))
        for transaction_date, description, amount, transaction_type, is_transfer in cash_rows:
            connection.execute(
                text(
                    """
                    insert into silver.cash_transactions (
                        account_id, transaction_date, description_raw, amount, direction,
                        transaction_type, is_transfer
                    )
                    values (
                        :account_id, :transaction_date, :description, :amount, 'outflow',
                        :transaction_type, :is_transfer
                    )
                    """
                ),
                {
                    "account_id": account_id,
                    "transaction_date": transaction_date,
                    "description": description,
                    "amount": amount,
                    "transaction_type": transaction_type,
                    "is_transfer": is_transfer,
                },
            )

        card_id = connection.execute(
            text(
                """
                insert into silver.cards (institution, card_name)
                values ('Sicoob', 'Sicoob Visa')
                returning id
                """
            )
        ).scalar_one()
        invoice_id = connection.execute(
            text(
                """
                insert into silver.card_invoices (card_id, reference_month, due_date, total_amount)
                values (:card_id, date '2026-06-01', date '2026-06-11', 0.00)
                returning id
                """
            ),
            {"card_id": card_id},
        ).scalar_one()
        transaction_id = connection.execute(
            text(
                """
                insert into silver.card_transactions (
                    invoice_id, card_id, purchase_date, description_raw, amount
                )
                values (:invoice_id, :card_id, date '2026-06-05', 'Parcela futura', 0.00)
                returning id
                """
            ),
            {"invoice_id": invoice_id, "card_id": card_id},
        ).scalar_one()
        connection.execute(
            text(
                """
                insert into silver.installments (
                    card_transaction_id, installment_number, installment_total, installment_amount, due_month
                )
                values
                    (:transaction_id, 2, 3, 150.00, date '2026-07-01'),
                    (:transaction_id, 3, 3, 150.00, date '2026-08-01')
                """
            ),
            {"transaction_id": transaction_id},
        )


def _asset(connection, code: str, name: str, asset_class: str, institution: str, reserve: bool):
    return connection.execute(
        text(
            """
            insert into silver.investment_assets (
                asset_code, asset_name, asset_class, institution, default_counts_as_reserve
            )
            values (:code, :name, :asset_class, :institution, :reserve)
            returning id
            """
        ),
        {
            "code": code,
            "name": name,
            "asset_class": asset_class,
            "institution": institution,
            "reserve": reserve,
        },
    ).scalar_one()


def test_gold_refresh_calculates_required_indicators(client: TestClient) -> None:
    seed_silver(include_contribution=True)

    response = client.post("/gold/refresh", params={"reference_date": "2026-06-30"})
    assert response.status_code == 200, response.text
    assert response.json()["refreshed"]["financial_alerts"] == 1

    passive = client.get("/gold/passive-income").json()[0]
    assert d(passive["received_amount"]) == Decimal("300.00")
    assert d(passive["avg_3m_received"]) == Decimal("200.00")
    assert d(passive["avg_12m_received"]) == Decimal("50.00")
    assert d(passive["progress_pct"]) == Decimal("6.00")

    goal = client.get("/gold/goal-100k").json()[0]
    assert d(goal["invested_amount"]) == Decimal("26000.00")
    assert d(goal["remaining_amount"]) == Decimal("74000.00")
    assert d(goal["avg_monthly_contribution"]) == Decimal("100.00")
    assert goal["estimated_months_to_goal"] == 740

    reserve = client.get("/gold/reserve").json()[0]
    assert d(reserve["avg_monthly_expenses_3m"]) == Decimal("1000.00")
    assert d(reserve["reserve_target"]) == Decimal("6000.00")
    assert d(reserve["eligible_reserve_amount"]) == Decimal("6000.00")
    assert reserve["status"] == "complete"

    allocation = client.get("/gold/allocation").json()
    assert sum(d(item["amount"]) for item in allocation) == Decimal("26000.00")
    reserve_allocations = [item for item in allocation if item["counts_as_reserve"]]
    assert len(reserve_allocations) == 1
    assert reserve_allocations[0]["asset_class"] == "cdb"

    commitments = client.get("/gold/future-commitments").json()
    assert len(commitments) == 2
    context = client.get("/gold/decision-context").json()[0]
    assert d(context["minimum_monthly_contribution"]) == Decimal("300.00")
    assert d(context["future_commitments_next_month"]) == Decimal("150.00")

    alert = client.get("/gold/alerts").json()[0]
    assert alert["alert_type"] == "minimum_contribution"
    assert alert["severity"] == "info"


def test_gold_refresh_warns_when_minimum_contribution_is_missing(client: TestClient) -> None:
    seed_silver(include_contribution=False)

    response = client.post("/gold/refresh", params={"reference_date": "2026-06-30"})
    assert response.status_code == 200

    alert = client.get("/gold/alerts").json()[0]
    assert alert["severity"] == "warning"
    assert d(alert["payload"]["actual_contribution"]) == Decimal("0.00")
