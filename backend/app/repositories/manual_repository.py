from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.repositories.silver_repository import SilverRepository
from app.services.import_review import _asset_code
from app.parsers.utils import normalize_text


DEFAULT_CATEGORIES = (
    ("Moradia", "expense"),
    ("Alimentacao", "expense"),
    ("Delivery", "expense"),
    ("Transporte", "expense"),
    ("Tecnologia", "expense"),
    ("Educacao", "expense"),
    ("Saude", "expense"),
    ("Lazer", "expense"),
    ("Assinaturas", "expense"),
    ("Investimentos", "transfer"),
    ("Transferencias", "transfer"),
    ("Dividas", "expense"),
    ("Impostos/Taxas", "expense"),
    ("Previdencia", "investment"),
    ("Renda", "income"),
    ("Renda passiva", "income"),
    ("Outros", "expense"),
    ("Nao classificado", "expense"),
)


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
        self.seed_default_categories()
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
                on conflict (name, type)
                do update set is_system = app.categories.is_system or excluded.is_system
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

    def seed_default_categories(self) -> None:
        for name, category_type in DEFAULT_CATEGORIES:
            self.session.execute(
                text(
                    """
                    insert into app.categories (name, type, is_system)
                    values (:name, :type, true)
                    on conflict (name, type)
                    do update set is_system = true
                    """
                ),
                {"name": name, "type": category_type},
            )
        self.session.commit()

    def list_categorization_rules(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select
                    rule.id,
                    rule.pattern,
                    rule.match_type,
                    rule.category_id,
                    category.name as category_name,
                    rule.transaction_type,
                    rule.priority,
                    rule.confidence_score,
                    rule.is_active,
                    rule.created_at,
                    rule.updated_at
                from app.categorization_rules rule
                join app.categories category on category.id = rule.category_id
                order by rule.priority asc, rule.confidence_score desc, rule.created_at asc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_categorization_rule(self, payload: Any) -> dict[str, Any]:
        data = _payload_all(payload)
        row = self.session.execute(
            text(
                """
                insert into app.categorization_rules (
                    pattern,
                    match_type,
                    category_id,
                    transaction_type,
                    priority,
                    confidence_score,
                    is_active
                )
                values (
                    :pattern,
                    :match_type,
                    :category_id,
                    :transaction_type,
                    :priority,
                    :confidence_score,
                    :is_active
                )
                returning id
                """
            ),
            data,
        ).scalar_one()
        result = self.get_categorization_rule(row)
        self.audit(entity_schema="app", entity_table="categorization_rules", entity_id=row, action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_categorization_rule(self, rule_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select
                        rule.id,
                        rule.pattern,
                        rule.match_type,
                        rule.category_id,
                        category.name as category_name,
                        rule.transaction_type,
                        rule.priority,
                        rule.confidence_score,
                        rule.is_active,
                        rule.created_at,
                        rule.updated_at
                    from app.categorization_rules rule
                    join app.categories category on category.id = rule.category_id
                    where rule.id = :id
                    """
                ),
                {"id": rule_id},
            ).mappings().one_or_none()
        )

    def update_categorization_rule(self, rule_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_categorization_rule(rule_id)
        if before is None:
            return None
        data = _payload(payload)
        if data:
            self._update("app", "categorization_rules", rule_id, data, touch_updated_at=True)
        after = self.get_categorization_rule(rule_id)
        self.audit(entity_schema="app", entity_table="categorization_rules", entity_id=rule_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_categorization_rule(self, rule_id: UUID) -> bool:
        before = self.get_categorization_rule(rule_id)
        if before is None:
            return False
        self.session.execute(text("delete from app.categorization_rules where id = :id"), {"id": rule_id})
        self.audit(entity_schema="app", entity_table="categorization_rules", entity_id=rule_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def preview_category(self, payload: Any) -> dict[str, Any]:
        self.seed_default_categories()
        description = payload.description
        transaction_type = payload.transaction_type
        normalized_description = normalize_text(description)
        for rule in self.list_categorization_rules():
            if not rule["is_active"]:
                continue
            if rule["transaction_type"] and rule["transaction_type"] != transaction_type:
                continue
            pattern = normalize_text(rule["pattern"])
            match rule["match_type"]:
                case "exact":
                    matched = normalized_description == pattern
                case "startswith":
                    matched = normalized_description.startswith(pattern)
                case _:
                    matched = pattern in normalized_description
            if matched:
                return {
                    "description": description,
                    "transaction_type": transaction_type,
                    "category_id": rule["category_id"],
                    "category_name": rule["category_name"],
                    "matched_rule_id": rule["id"],
                    "confidence_score": rule["confidence_score"],
                    "needs_review": rule["confidence_score"] < Decimal("0.7000"),
                }

        fallback = self.session.execute(
            text(
                """
                select id, name
                from app.categories
                where name = 'Nao classificado'
                order by type
                limit 1
                """
            )
        ).mappings().one_or_none()
        return {
            "description": description,
            "transaction_type": transaction_type,
            "category_id": fallback["id"] if fallback else None,
            "category_name": fallback["name"] if fallback else None,
            "matched_rule_id": None,
            "confidence_score": Decimal("0.0000"),
            "needs_review": True,
        }

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

    def list_cards(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select id, institution, card_name, brand, last_four_digits, credit_limit, is_active, created_at
                from silver.cards
                order by created_at desc, id desc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_card(self, payload: Any) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                insert into silver.cards (institution, card_name, brand, last_four_digits, credit_limit)
                values (:institution, :card_name, :brand, :last_four_digits, :credit_limit)
                returning id, institution, card_name, brand, last_four_digits, credit_limit, is_active, created_at
                """
            ),
            _payload_all(payload),
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="silver", entity_table="cards", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_card(self, card_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select id, institution, card_name, brand, last_four_digits, credit_limit, is_active, created_at
                    from silver.cards
                    where id = :id
                    """
                ),
                {"id": card_id},
            ).mappings().one_or_none()
        )

    def update_card(self, card_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_card(card_id)
        if before is None:
            return None
        data = _payload(payload)
        if data:
            self._update("silver", "cards", card_id, data)
        after = self.get_card(card_id)
        self.audit(entity_schema="silver", entity_table="cards", entity_id=card_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_card(self, card_id: UUID) -> bool:
        before = self.get_card(card_id)
        if before is None:
            return False
        self.session.execute(text("delete from silver.cards where id = :id"), {"id": card_id})
        self.audit(entity_schema="silver", entity_table="cards", entity_id=card_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def list_card_invoices(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select
                    id,
                    card_id,
                    reference_month,
                    closing_date,
                    due_date,
                    total_amount,
                    minimum_payment,
                    credit_limit,
                    used_limit,
                    available_limit,
                    next_invoice_committed_amount,
                    future_debt_total,
                    status,
                    created_at
                from silver.card_invoices
                order by reference_month desc, id desc
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_card_invoice(self, payload: Any) -> dict[str, Any]:
        data = _payload_all(payload)
        row = self.session.execute(
            text(
                """
                insert into silver.card_invoices (
                    card_id,
                    reference_month,
                    closing_date,
                    due_date,
                    total_amount,
                    minimum_payment,
                    credit_limit,
                    used_limit,
                    available_limit,
                    next_invoice_committed_amount,
                    future_debt_total,
                    status
                )
                values (
                    :card_id,
                    :reference_month,
                    :closing_date,
                    :due_date,
                    :total_amount,
                    :minimum_payment,
                    :credit_limit,
                    :used_limit,
                    :available_limit,
                    :next_invoice_committed_amount,
                    :future_debt_total,
                    :status
                )
                returning
                    id,
                    card_id,
                    reference_month,
                    closing_date,
                    due_date,
                    total_amount,
                    minimum_payment,
                    credit_limit,
                    used_limit,
                    available_limit,
                    next_invoice_committed_amount,
                    future_debt_total,
                    status,
                    created_at
                """
            ),
            data,
        ).mappings().one()
        result = dict(row)
        self.audit(entity_schema="silver", entity_table="card_invoices", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def get_card_invoice(self, invoice_id: UUID) -> dict[str, Any] | None:
        return _dict(
            self.session.execute(
                text(
                    """
                    select
                        id,
                        card_id,
                        reference_month,
                        closing_date,
                        due_date,
                        total_amount,
                        minimum_payment,
                        credit_limit,
                        used_limit,
                        available_limit,
                        next_invoice_committed_amount,
                        future_debt_total,
                        status,
                        created_at
                    from silver.card_invoices
                    where id = :id
                    """
                ),
                {"id": invoice_id},
            ).mappings().one_or_none()
        )

    def update_card_invoice(self, invoice_id: UUID, payload: Any) -> dict[str, Any] | None:
        before = self.get_card_invoice(invoice_id)
        if before is None:
            return None
        data = _payload(payload)
        if data:
            self._update("silver", "card_invoices", invoice_id, data)
        after = self.get_card_invoice(invoice_id)
        self.audit(entity_schema="silver", entity_table="card_invoices", entity_id=invoice_id, action="update", before=before, after=after)
        self.session.commit()
        return after

    def delete_card_invoice(self, invoice_id: UUID) -> bool:
        before = self.get_card_invoice(invoice_id)
        if before is None:
            return False
        self.session.execute(
            text(
                """
                delete from silver.installments
                where card_transaction_id in (
                    select id from silver.card_transactions where invoice_id = :id
                )
                """
            ),
            {"id": invoice_id},
        )
        self.session.execute(text("delete from silver.card_transactions where invoice_id = :id"), {"id": invoice_id})
        self.session.execute(text("delete from silver.card_invoices where id = :id"), {"id": invoice_id})
        self.audit(entity_schema="silver", entity_table="card_invoices", entity_id=invoice_id, action="delete", before=before, after=None)
        self.session.commit()
        return True

    def create_card_transaction(self, invoice_id: UUID, payload: Any) -> dict[str, Any] | None:
        invoice = self.get_card_invoice(invoice_id)
        if invoice is None:
            return None
        data = _payload_all(payload)
        card_id = invoice["card_id"]
        is_installment = data["installment_total"] > 1
        row = self.session.execute(
            text(
                """
                insert into silver.card_transactions (
                    invoice_id,
                    card_id,
                    purchase_date,
                    description_raw,
                    amount,
                    category_id,
                    installment_number,
                    installment_total,
                    is_installment,
                    raw_reference,
                    confidence_score,
                    needs_review
                )
                values (
                    :invoice_id,
                    :card_id,
                    :purchase_date,
                    :description_raw,
                    :amount,
                    :category_id,
                    :installment_number,
                    :installment_total,
                    :is_installment,
                    cast(:raw_reference as jsonb),
                    1.0000,
                    false
                )
                returning
                    id,
                    invoice_id,
                    card_id,
                    purchase_date,
                    description_raw,
                    amount,
                    category_id,
                    installment_number,
                    installment_total,
                    is_installment,
                    created_at
                """
            ),
            {
                **data,
                "invoice_id": invoice_id,
                "card_id": card_id,
                "is_installment": is_installment,
                "raw_reference": _json({"source_type": "manual_card_invoice"}),
            },
        ).mappings().one()
        result = dict(row)
        self._create_installments_for_card_transaction(result, invoice["reference_month"])
        self.audit(entity_schema="silver", entity_table="card_transactions", entity_id=result["id"], action="create", before=None, after=result)
        self.session.commit()
        return result

    def _create_installments_for_card_transaction(self, transaction: dict[str, Any], reference_month: date) -> None:
        installment_total = transaction["installment_total"]
        installment_number = transaction["installment_number"]
        if installment_total <= 1:
            self.session.execute(
                text(
                    """
                    insert into silver.installments (
                        card_transaction_id,
                        installment_number,
                        installment_total,
                        installment_amount,
                        due_month
                    )
                    values (:id, 1, 1, :amount, :due_month)
                    """
                ),
                {
                    "id": transaction["id"],
                    "amount": transaction["amount"],
                    "due_month": date(reference_month.year, reference_month.month, 1),
                },
            )
            return

        first_due_month = date(reference_month.year, reference_month.month, 1)
        for number in range(installment_number, installment_total + 1):
            self.session.execute(
                text(
                    """
                    insert into silver.installments (
                        card_transaction_id,
                        installment_number,
                        installment_total,
                        installment_amount,
                        due_month
                    )
                    values (:id, :number, :total, :amount, :due_month)
                    """
                ),
                {
                    "id": transaction["id"],
                    "number": number,
                    "total": installment_total,
                    "amount": transaction["amount"],
                    "due_month": _add_months(first_due_month, number - installment_number),
                },
            )

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


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)
