from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class PurchaseDecisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def latest_context(self, reference_date: date) -> dict[str, Any] | None:
        row = self.session.execute(
            text(
                """
                select
                    reference_date,
                    net_income,
                    minimum_monthly_contribution,
                    reserve_target,
                    eligible_reserve_amount,
                    invested_amount,
                    goal_100k_remaining,
                    future_commitments_next_month,
                    available_after_commitments
                from gold.purchase_decision_context
                where reference_date <= :reference_date
                order by reference_date desc, created_at desc
                limit 1
                """
            ),
            {"reference_date": reference_date},
        ).mappings().one_or_none()
        return dict(row) if row is not None else None

    def current_cash_balance(self, reference_date: date) -> Decimal:
        return self.session.execute(
            text(
                """
                select coalesce(sum(amount), 0)
                from silver.cash_transactions
                where transaction_date <= :reference_date
                """
            ),
            {"reference_date": reference_date},
        ).scalar_one()

    def insert_decision(
        self,
        *,
        decision_date: date,
        item_name: str,
        amount: Decimal,
        category_id: UUID | None,
        is_planned: bool,
        is_technology: bool,
        payment_method: str,
        installments: int,
        monthly_installment: Decimal,
        urgency: str,
        justification: str | None,
        verdict: str,
        reserve_impact_amount: Decimal,
        contribution_impact_amount: Decimal,
        goal_100k_delay_days: int,
        future_commitment_impact: Decimal,
        explanation: str,
    ) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                insert into app.purchase_decisions (
                    decision_date,
                    item_name,
                    amount,
                    category_id,
                    is_planned,
                    is_technology,
                    payment_method,
                    installments,
                    monthly_installment,
                    urgency,
                    justification,
                    verdict,
                    reserve_impact_amount,
                    contribution_impact_amount,
                    goal_100k_delay_days,
                    future_commitment_impact,
                    explanation
                )
                values (
                    :decision_date,
                    :item_name,
                    :amount,
                    :category_id,
                    :is_planned,
                    :is_technology,
                    :payment_method,
                    :installments,
                    :monthly_installment,
                    :urgency,
                    :justification,
                    :verdict,
                    :reserve_impact_amount,
                    :contribution_impact_amount,
                    :goal_100k_delay_days,
                    :future_commitment_impact,
                    :explanation
                )
                returning
                    id,
                    decision_date,
                    item_name,
                    amount,
                    category_id,
                    is_planned,
                    is_technology,
                    payment_method,
                    installments,
                    monthly_installment,
                    urgency,
                    justification,
                    verdict,
                    reserve_impact_amount,
                    contribution_impact_amount,
                    goal_100k_delay_days,
                    future_commitment_impact,
                    explanation,
                    created_at
                """
            ),
            {
                "decision_date": decision_date,
                "item_name": item_name,
                "amount": amount,
                "category_id": category_id,
                "is_planned": is_planned,
                "is_technology": is_technology,
                "payment_method": payment_method,
                "installments": installments,
                "monthly_installment": monthly_installment,
                "urgency": urgency,
                "justification": justification,
                "verdict": verdict,
                "reserve_impact_amount": reserve_impact_amount,
                "contribution_impact_amount": contribution_impact_amount,
                "goal_100k_delay_days": goal_100k_delay_days,
                "future_commitment_impact": future_commitment_impact,
                "explanation": explanation,
            },
        ).mappings().one()
        self.session.commit()
        return dict(row)

    def list_decisions(self, limit: int) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select
                    id,
                    decision_date,
                    item_name,
                    amount,
                    category_id,
                    is_planned,
                    is_technology,
                    payment_method,
                    installments,
                    monthly_installment,
                    urgency,
                    justification,
                    verdict,
                    reserve_impact_amount,
                    contribution_impact_amount,
                    goal_100k_delay_days,
                    future_commitment_impact,
                    explanation,
                    created_at
                from app.purchase_decisions
                order by decision_date desc, created_at desc
                limit :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
        return [dict(row) for row in rows]
