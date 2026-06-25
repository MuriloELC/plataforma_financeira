from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.main import create_app


def _assert_ok(response, expected_status: int) -> dict:
    if response.status_code != expected_status:
        raise AssertionError(f"Expected {expected_status}, got {response.status_code}: {response.text}")
    if response.status_code == 204:
        return {}
    return response.json()


def main() -> int:
    get_settings.cache_clear()
    client = TestClient(create_app())
    today = date.today().isoformat()

    categories = _assert_ok(client.get("/categories"), 200)
    technology = next((item for item in categories if item["name"] == "Tecnologia"), None)
    if technology is None:
        raise AssertionError("Default Tecnologia category was not seeded.")
    _assert_ok(
        client.post(
            "/categorization-rules",
            json={
                "pattern": "notebook",
                "category_id": technology["id"],
                "match_type": "contains",
                "priority": 1,
                "confidence_score": "0.9500",
            },
        ),
        201,
    )
    category_preview = _assert_ok(
        client.post("/categorize/preview", json={"description": "Compra notebook anonima"}),
        200,
    )
    if category_preview["category_name"] != "Tecnologia":
        raise AssertionError("Categorization preview did not match Tecnologia.")

    fixture = Path("/fixtures/anonymized/mercado_livre/account_statement_sample.csv")
    if not fixture.exists():
        fixture = Path("fixtures/anonymized/mercado_livre/account_statement_sample.csv")

    with fixture.open("rb") as file_handle:
        upload = _assert_ok(
            client.post(
                "/files/upload",
                files={"file": (fixture.name, file_handle, "text/csv")},
            ),
            201,
        )
    batch_id = upload["import_batch"]["id"]

    preview = _assert_ok(client.get(f"/import-batches/{batch_id}/preview"), 200)
    if not preview["records"]:
        raise AssertionError("Preview did not return parsed records.")

    approval = _assert_ok(client.post(f"/import-batches/{batch_id}/approve"), 200)
    if approval["silver_counts"].get("cash_transactions", 0) == 0:
        raise AssertionError("Approval did not create Silver cash transactions.")

    _assert_ok(client.post(f"/gold/refresh?reference_date={today}"), 200)

    _assert_ok(
        client.post(
            "/manual/investments",
            json={
                "institution": "Mercado Livre",
                "product_name": "CDB Anonimo Fluxo MVP",
                "asset_class": "cdb",
                "reference_date": today,
                "gross_value": "1000.00",
                "net_value": "1000.00",
                "liquidity": "daily",
                "counts_as_reserve": True,
            },
        ),
        201,
    )

    card = _assert_ok(
        client.post(
            "/cards",
            json={
                "institution": "Sicoob",
                "card_name": "Cartao MVP",
                "brand": "Visa",
                "last_four_digits": "1234",
                "credit_limit": "5000.00",
            },
        ),
        201,
    )
    invoice = _assert_ok(
        client.post(
            "/card-invoices",
            json={
                "card_id": card["id"],
                "reference_month": today[:8] + "01",
                "due_date": today,
                "total_amount": "300.00",
                "minimum_payment": "50.00",
            },
        ),
        201,
    )
    _assert_ok(
        client.post(
            f"/card-invoices/{invoice['id']}/transactions",
            json={
                "purchase_date": today,
                "description_raw": "Compra parcelada MVP",
                "amount": "100.00",
                "installment_number": 1,
                "installment_total": 3,
            },
        ),
        201,
    )

    _assert_ok(client.post(f"/gold/refresh?reference_date={today}"), 200)

    for endpoint in (
        "/gold/passive-income?limit=1",
        "/gold/goal-100k?limit=1",
        "/gold/reserve?limit=1",
        "/gold/allocation?limit=20",
        "/gold/decision-context?limit=1",
    ):
        _assert_ok(client.get(endpoint), 200)

    simulation = _assert_ok(
        client.post(
            "/purchase-decisions/simulate",
            json={
                "item": "Compra anonima de validacao",
                "amount": "50.00",
                "payment_method": "pix",
                "installments": 1,
                "reason": "Validacao do fluxo principal",
                "urgency": "baixa",
                "is_planned": True,
                "is_technology": False,
                "justification": "Validacao automatizada do fluxo MVP.",
                "decision_date": today,
            },
        ),
        200,
    )
    if not simulation.get("decision_id"):
        raise AssertionError("Simulation did not save a purchase decision.")

    history = _assert_ok(client.get("/purchase-decisions?limit=5"), 200)
    if not any(item["id"] == simulation["decision_id"] for item in history):
        raise AssertionError("Saved decision was not returned in history.")

    print("MVP flow validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
