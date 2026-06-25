from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.repositories.silver_repository import SilverRepository
from app.services.import_review import _asset_code


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def _dict(row: RowMapping | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _payload(model: Any) -> dict[str, Any]:
    return model.model_dump(exclude_unset=True)


def _payload_all(model: Any) -> dict[str, Any]:
    return model.model_dump()


class ManualRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.silver = SilverRepository(session)

    def audit(
        self,
        *,
        entity_schema: str,
        entity_table: str,
        entity_id: UUID | None,
        action: str,
        before: Mapping[str, Any] | None,
        after: Mapping[str, Any] | None,
        reason: str | None = None,
    ) -> None:
        self.session.execute(
            text(
                """
                insert into app.audit_logs (
                    entity_schema,
                    entity_table,
                    entity_id,
                    action,
                    reason,
                    before_payload,
                    after_payload
                )
                values (
                    :entity_schema,
                    :entity_table,
                    :entity_id,
                    :action,
                    :reason,
                    cast(:before_payload as jsonb),
                    cast(:after_payload as jsonb)
                )
                """
            ),
            {
                "entity_schema": entity_schema,
                "entity_table": entity_table,
                "entity_id": entity_id,
                "action": action,
                "reason": reason,
                "before_payload": _json(before) if before is not None else None,
                "after_payload": _json(after) if after is not None else None,
            },
        )

    def list_accounts(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select id, institution, account_name, account_type, is_active, created_at
                from silver.accounts
                order by created_at desc, id desc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_account(self, payload: Any) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                insert into silver.accounts (institution, account_name, account_type)
                values (:institution, :account_name, :account_type)
                returning id, institution, account_name, account_type, is_active, created_at
                """
            ),
            _payload_all(payload),
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="silver", entity_table="accounts", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_account(self, account_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select id, institution, account_name, account_type, is_active, created_at
                    from silver.accounts
                    where id = :id
                    """
                ),
                {"id": account_id},
            ).mappings().one_or_none()
        )

    def update_account(self, account_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_account(account_id)
        if before is None:
            return None
        data = _payload(payload)
        if data:
            self._update("silver", "accounts", account_id, data)
        after = self.get_account(account_id)
        self.audit(entity_schema="silver", entity_table="accounts", entity_id=account_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_account(self, account_id: UUID) -> bool:
        before = self.get_account(account_id)
        if before is None:
            return False
        self.session.execute(text("delete from silver.accounts where id = :id"), {"id": account_id})
        self.audit(entity_schema="silver", entity_table="accounts", entity_id=account_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def list_categories(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select id, name, parent_id, type, is_system, created_at
                from app.categories
                order by name
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_category(self, payload: Any) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                insert into app.categories (name, parent_id, type, is_system)
                values (:name, :parent_id, :type, :is_system)
                returning id, name, parent_id, type, is_system, created_at
                """
            ),
            _payload_all(payload),
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="app", entity_table="categories", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_category(self, category_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select id, name, parent_id, type, is_system, created_at
                    from app.categories
                    where id = :id
                    """
                ),
                {"id": category_id},
            ).mappings().one_or_none()
        )

    def update_category(self, category_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_category(category_id)
        if before is None:
            return None
        data = _payload(payload)
        if data:
            self._update("app", "categories", category_id, data)
        after = self.get_category(category_id)
        self.audit(entity_schema="app", entity_table="categories", entity_id=category_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_category(self, category_id: UUID) -> bool:
        before = self.get_category(category_id)
        if before is None:
            return False
        self.session.execute(text("delete from app.categories where id = :id"), {"id": category_id})
        self.audit(entity_schema="app", entity_table="categories", entity_id=category_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def list_goals(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select id, name, goal_type, target_amount, target_date, current_amount, status, metadata, created_at, updated_at
                from app.goals
                order by created_at desc, id desc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_goal(self, payload: Any) -> dict[str, Any]:
        data = _payload_all(payload)
        row = self.session.execute(
            text(
                """
                insert into app.goals (
                    name,
                    goal_type,
                    target_amount,
                    target_date,
                    current_amount,
                    status,
                    metadata
                )
                values (
                    :name,
                    :goal_type,
                    :target_amount,
                    :target_date,
                    :current_amount,
                    :status,
                    cast(:metadata as jsonb)
                )
                returning id, name, goal_type, target_amount, target_date, current_amount, status, metadata, created_at, updated_at
                """
            ),
            {**data, "metadata": _json(data.get("metadata", {}))},
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="app", entity_table="goals", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_goal(self, goal_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select id, name, goal_type, target_amount, target_date, current_amount, status, metadata, created_at, updated_at
                    from app.goals
                    where id = :id
                    """
                ),
                {"id": goal_id},
            ).mappings().one_or_none()
        )

    def update_goal(self, goal_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_goal(goal_id)
        if before is None:
            return None
        data = _payload(payload)
        if "metadata" in data:
            data["metadata"] = _json(data["metadata"])
        if data:
            self._update("app", "goals", goal_id, data, jsonb_fields={"metadata"}, touch_updated_at=True)
        after = self.get_goal(goal_id)
        self.audit(entity_schema="app", entity_table="goals", entity_id=goal_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_goal(self, goal_id: UUID) -> bool:
        before = self.get_goal(goal_id)
        if before is None:
            return False
        self.session.execute(text("delete from app.goals where id = :id"), {"id": goal_id})
        self.audit(entity_schema="app", entity_table="goals", entity_id=goal_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def list_manual_transactions(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select
                    id,
                    account_id,
                    transaction_date,
                    description_raw,
                    amount,
                    direction,
                    category_id,
                    transaction_type,
                    is_transfer,
                    is_recurring,
                    raw_reference ->> 'notes' as notes,
                    created_at
                from silver.cash_transactions
                where transaction_type = 'manual'
                order by transaction_date desc, id desc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_manual_transaction(self, payload: Any) -> dict[str, Any]:
        data = _payload_all(payload)
        direction = "inflow" if data["amount"] >= Decimal("0") else "outflow"
        row = self.session.execute(
            text(
                """
                insert into silver.cash_transactions (
                    account_id,
                    transaction_date,
                    description_raw,
                    amount,
                    direction,
                    category_id,
                    transaction_type,
                    is_transfer,
                    is_recurring,
                    raw_reference,
                    confidence_score,
                    needs_review
                )
                values (
                    :account_id,
                    :transaction_date,
                    :description_raw,
                    :amount,
                    :direction,
                    :category_id,
                    :transaction_type,
                    :is_transfer,
                    :is_recurring,
                    cast(:raw_reference as jsonb),
                    1.0000,
                    false
                )
                returning
                    id,
                    account_id,
                    transaction_date,
                    description_raw,
                    amount,
                    direction,
                    category_id,
                    transaction_type,
                    is_transfer,
                    is_recurring,
                    raw_reference ->> 'notes' as notes,
                    created_at
                """
            ),
            {
                **data,
                "direction": direction,
                "raw_reference": _json({"source_type": "manual", "notes": data.get("notes")}),
            },
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="silver", entity_table="cash_transactions", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_manual_transaction(self, transaction_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select
                        id,
                        account_id,
                        transaction_date,
                        description_raw,
                        amount,
                        direction,
                        category_id,
                        transaction_type,
                        is_transfer,
                        is_recurring,
                        raw_reference ->> 'notes' as notes,
                        created_at
                    from silver.cash_transactions
                    where id = :id and transaction_type = 'manual'
                    """
                ),
                {"id": transaction_id},
            ).mappings().one_or_none()
        )

    def update_manual_transaction(self, transaction_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_manual_transaction(transaction_id)
        if before is None:
            return None
        data = _payload(payload)
        if "amount" in data:
            data["direction"] = "inflow" if data["amount"] >= Decimal("0") else "outflow"
        if "notes" in data:
            notes = data.pop("notes")
            data["raw_reference"] = _json({"source_type": "manual", "notes": notes})
        if data:
            self._update("silver", "cash_transactions", transaction_id, data, jsonb_fields={"raw_reference"})
        after = self.get_manual_transaction(transaction_id)
        self.audit(entity_schema="silver", entity_table="cash_transactions", entity_id=transaction_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_manual_transaction(self, transaction_id: UUID) -> bool:
        before = self.get_manual_transaction(transaction_id)
        if before is None:
            return False
        self.session.execute(text("delete from silver.cash_transactions where id = :id"), {"id": transaction_id})
        self.audit(entity_schema="silver", entity_table="cash_transactions", entity_id=transaction_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def list_manual_investments(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select
                    id,
                    asset_id,
                    institution,
                    product_name,
                    asset_class,
                    reference_date,
                    gross_value,
                    net_value,
                    liquidity,
                    maturity_date,
                    rate_description,
                    counts_as_reserve,
                    notes,
                    created_at,
                    updated_at
                from silver.manual_investment_positions
                order by reference_date desc, id desc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_manual_investment(self, payload: Any) -> dict[str, Any]:
        data = _payload_all(payload)
        asset_id = self.silver.find_or_create_asset(
            asset_code=_asset_code(data["product_name"]),
            asset_name=data["product_name"],
            asset_class=data["asset_class"],
            institution=data["institution"],
            counts_as_reserve=data["counts_as_reserve"],
        )
        row = self.session.execute(
            text(
                """
                insert into silver.manual_investment_positions (
                    asset_id,
                    institution,
                    product_name,
                    asset_class,
                    reference_date,
                    gross_value,
                    net_value,
                    liquidity,
                    maturity_date,
                    rate_description,
                    counts_as_reserve,
                    notes
                )
                values (
                    :asset_id,
                    :institution,
                    :product_name,
                    :asset_class,
                    :reference_date,
                    :gross_value,
                    :net_value,
                    :liquidity,
                    :maturity_date,
                    :rate_description,
                    :counts_as_reserve,
                    :notes
                )
                returning
                    id,
                    asset_id,
                    institution,
                    product_name,
                    asset_class,
                    reference_date,
                    gross_value,
                    net_value,
                    liquidity,
                    maturity_date,
                    rate_description,
                    counts_as_reserve,
                    notes,
                    created_at,
                    updated_at
                """
            ),
            {**data, "asset_id": asset_id},
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="silver", entity_table="manual_investment_positions", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_manual_investment(self, investment_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select
                        id,
                        asset_id,
                        institution,
                        product_name,
                        asset_class,
                        reference_date,
                        gross_value,
                        net_value,
                        liquidity,
                        maturity_date,
                        rate_description,
                        counts_as_reserve,
                        notes,
                        created_at,
                        updated_at
                    from silver.manual_investment_positions
                    where id = :id
                    """
                ),
                {"id": investment_id},
            ).mappings().one_or_none()
        )

    def update_manual_investment(self, investment_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_manual_investment(investment_id)
        if before is None:
            return None
        data = _payload(payload)
        if data:
            self._update("silver", "manual_investment_positions", investment_id, data, touch_updated_at=True)
        after = self.get_manual_investment(investment_id)
        self.audit(entity_schema="silver", entity_table="manual_investment_positions", entity_id=investment_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_manual_investment(self, investment_id: UUID) -> bool:
        before = self.get_manual_investment(investment_id)
        if before is None:
            return False
        self.session.execute(text("delete from silver.manual_investment_positions where id = :id"), {"id": investment_id})
        self.audit(entity_schema="silver", entity_table="manual_investment_positions", entity_id=investment_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def _update(
        self,
        schema: str,
        table: str,
        entity_id: UUID,
        data: dict[str, Any],
        *,
        jsonb_fields: set[str] | None = None,
        touch_updated_at: bool = False,
    ) -> None:
        jsonb_fields = jsonb_fields or set()
        assignments = []
        params: dict[str, Any] = {"id": entity_id}
        for key, value in data.items():
            params[key] = value
            if key in jsonb_fields:
                assignments.append(f"{key} = cast(:{key} as jsonb)")
            else:
                assignments.append(f"{key} = :{key}")
        if touch_updated_at:
            assignments.append("updated_at = now()")
        sql = f"update {schema}.{table} set {', '.join(assignments)} where id = :id"
        self.session.execute(text(sql), params)
