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
    "app.purchase_decisions",
    "gold.purchase_decision_context",
    "silver.cash_transactions",
    "silver.accounts",
)


@pytest.fixture(autouse=True)
def purchase_decision_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate purchase decisions with PostgreSQL.")

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


def seed_context(*, available: str, reserve_target: str, reserve_available: str) -> None:
    engine = create_database_engine()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                insert into gold.purchase_decision_context (
                    reference_date,
                    minimum_monthly_contribution,
                    reserve_target,
                    eligible_reserve_amount,
                    invested_amount,
                    goal_100k_remaining,
                    future_commitments_next_month,
                    available_after_commitments
                )
                values (
                    date '2026-06-30',
                    300.00,
                    :reserve_target,
                    :reserve_available,
                    26000.00,
                    74000.00,
                    100.00,
                    :available
                )
                """
            ),
            {
                "available": available,
                "reserve_target": reserve_target,
                "reserve_available": reserve_available,
            },
        )


def simulate(client: TestClient, **overrides: Any):
    payload = {
        "item": "Item teste",
        "amount": "100.00",
        "payment_method": "pix",
        "installments": 1,
        "reason": "necessidade documentada",
        "urgency": "baixa",
        "is_planned": True,
        "is_technology": False,
        "decision_date": "2026-06-30",
    }
    payload.update(overrides)
    return client.post("/purchase-decisions/simulate", json=payload)


def test_simulator_returns_comprar_agora_and_saves_history(client: TestClient) -> None:
    seed_context(available="2000.00", reserve_target="6000.00", reserve_available="10000.00")

    response = simulate(client)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verdict"] == "Comprar agora"
    assert "score" not in body
    assert body["requires_justification"] is False

    history = client.get("/purchase-decisions")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["verdict"] == "Comprar agora"


def test_simulator_returns_comprar_com_ajuste_when_contribution_is_justified(client: TestClient) -> None:
    seed_context(available="500.00", reserve_target="6000.00", reserve_available="10000.00")

    response = simulate(
        client,
        amount="250.00",
        justification="Vou compensar reduzindo gasto variavel no mes.",
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verdict"] == "Comprar com ajuste"
    assert body["requires_justification"] is True
    assert body["contribution_impact_amount"] == "50.00"
    assert body["goal_100k_delay_days"] > 0


def test_simulator_returns_esperar_when_purchase_drops_reserve_below_target(client: TestClient) -> None:
    seed_context(available="2000.00", reserve_target="6000.00", reserve_available="6200.00")

    response = simulate(client, amount="500.00", is_planned=False)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verdict"] == "Esperar"
    assert body["reserve_impact_amount"] == "300.00"


def test_simulator_returns_evitar_when_cash_and_reserve_are_insufficient(client: TestClient) -> None:
    seed_context(available="100.00", reserve_target="6000.00", reserve_available="500.00")

    response = simulate(
        client,
        amount="1000.00",
        is_planned=False,
        justification="Nao ha compensacao real.",
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verdict"] == "Evitar"
    assert body["contribution_impact_amount"] == "1200.00"


def test_simulator_requires_justification_for_technology_above_300(client: TestClient) -> None:
    seed_context(available="2000.00", reserve_target="6000.00", reserve_available="10000.00")

    response = simulate(
        client,
        item="Notebook",
        amount="1500.00",
        payment_method="credit_card",
        installments=10,
        is_technology=True,
        reason="upgrade de equipamento",
        justification=None,
    )

    assert response.status_code == 422
    assert "Justificativa obrigatoria" in response.json()["detail"]


def test_simulator_requires_justification_when_minimum_contribution_is_compromised(client: TestClient) -> None:
    seed_context(available="500.00", reserve_target="6000.00", reserve_available="10000.00")

    response = simulate(client, amount="250.00", justification=None)

    assert response.status_code == 422
    assert client.get("/purchase-decisions").json() == []
