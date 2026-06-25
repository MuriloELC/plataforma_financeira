from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


class GoldRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> None:
        self.session.execute(text(sql), params or {})

    def scalar(self, sql: str, params: Mapping[str, Any] | None = None) -> Any:
        return self.session.execute(text(sql), params or {}).scalar_one()

    def rows(self, sql: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return [dict(row) for row in self.session.execute(text(sql), params or {}).mappings().all()]

    def replace_passive_income(
        self,
        *,
        month: date,
        received_amount: Decimal,
        accrued_amount: Decimal,
        avg_3m_received: Decimal,
        avg_12m_received: Decimal,
        progress_pct: Decimal,
    ) -> None:
        self.execute("delete from gold.passive_income_monthly where month = :month", {"month": month})
        self.execute(
            """
            insert into gold.passive_income_monthly (
                month,
                received_amount,
                accrued_amount,
                avg_3m_received,
                avg_12m_received,
                progress_pct
            )
            values (
                :month,
                :received_amount,
                :accrued_amount,
                :avg_3m_received,
                :avg_12m_received,
                :progress_pct
            )
            """,
            {
                "month": month,
                "received_amount": received_amount,
                "accrued_amount": accrued_amount,
                "avg_3m_received": avg_3m_received,
                "avg_12m_received": avg_12m_received,
                "progress_pct": progress_pct,
            },
        )

    def replace_goal_100k(
        self,
        *,
        reference_date: date,
        invested_amount: Decimal,
        remaining_amount: Decimal,
        progress_pct: Decimal,
        avg_monthly_contribution: Decimal | None,
        estimated_months_to_goal: int | None,
    ) -> None:
        self.execute("delete from gold.goal_100k_progress where reference_date = :reference_date", {"reference_date": reference_date})
        self.execute(
            """
            insert into gold.goal_100k_progress (
                reference_date,
                invested_amount,
                remaining_amount,
                progress_pct,
                avg_monthly_contribution,
                estimated_months_to_goal
            )
            values (
                :reference_date,
                :invested_amount,
                :remaining_amount,
                :progress_pct,
                :avg_monthly_contribution,
                :estimated_months_to_goal
            )
            """,
            {
                "reference_date": reference_date,
                "invested_amount": invested_amount,
                "remaining_amount": remaining_amount,
                "progress_pct": progress_pct,
                "avg_monthly_contribution": avg_monthly_contribution,
                "estimated_months_to_goal": estimated_months_to_goal,
            },
        )

    def replace_reserve_status(
        self,
        *,
        reference_date: date,
        avg_monthly_expenses_3m: Decimal,
        reserve_target: Decimal,
        eligible_reserve_amount: Decimal,
        gap_amount: Decimal,
        status: str,
    ) -> None:
        self.execute("delete from gold.reserve_status where reference_date = :reference_date", {"reference_date": reference_date})
        self.execute(
            """
            insert into gold.reserve_status (
                reference_date,
                avg_monthly_expenses_3m,
                reserve_target,
                eligible_reserve_amount,
                gap_amount,
                status
            )
            values (
                :reference_date,
                :avg_monthly_expenses_3m,
                :reserve_target,
                :eligible_reserve_amount,
                :gap_amount,
                :status
            )
            """,
            {
                "reference_date": reference_date,
                "avg_monthly_expenses_3m": avg_monthly_expenses_3m,
                "reserve_target": reserve_target,
                "eligible_reserve_amount": eligible_reserve_amount,
                "gap_amount": gap_amount,
                "status": status,
            },
        )

    def replace_allocation(self, *, reference_date: date, allocations: list[dict[str, Any]]) -> None:
        self.execute("delete from gold.portfolio_allocation where reference_date = :reference_date", {"reference_date": reference_date})
        for item in allocations:
            self.execute(
                """
                insert into gold.portfolio_allocation (
                    reference_date,
                    asset_class,
                    amount,
                    allocation_pct,
                    counts_as_reserve
                )
                values (
                    :reference_date,
                    :asset_class,
                    :amount,
                    :allocation_pct,
                    :counts_as_reserve
                )
                """,
                {"reference_date": reference_date, **item},
            )

    def replace_future_commitments(self, *, month_start: date, commitments: list[dict[str, Any]]) -> None:
        self.execute("delete from gold.future_commitments where due_month >= :month_start", {"month_start": month_start})
        for item in commitments:
            self.execute(
                """
                insert into gold.future_commitments (
                    due_month,
                    source,
                    description,
                    amount,
                    commitment_type
                )
                values (
                    :due_month,
                    :source,
                    :description,
                    :amount,
                    :commitment_type
                )
                """,
                item,
            )

    def replace_purchase_context(
        self,
        *,
        reference_date: date,
        minimum_monthly_contribution: Decimal,
        reserve_target: Decimal,
        eligible_reserve_amount: Decimal,
        invested_amount: Decimal,
        goal_100k_remaining: Decimal,
        future_commitments_next_month: Decimal,
    ) -> None:
        self.execute("delete from gold.purchase_decision_context where reference_date = :reference_date", {"reference_date": reference_date})
        self.execute(
            """
            insert into gold.purchase_decision_context (
                reference_date,
                minimum_monthly_contribution,
                reserve_target,
                eligible_reserve_amount,
                invested_amount,
                goal_100k_remaining,
                future_commitments_next_month
            )
            values (
                :reference_date,
                :minimum_monthly_contribution,
                :reserve_target,
                :eligible_reserve_amount,
                :invested_amount,
                :goal_100k_remaining,
                :future_commitments_next_month
            )
            """,
            {
                "reference_date": reference_date,
                "minimum_monthly_contribution": minimum_monthly_contribution,
                "reserve_target": reserve_target,
                "eligible_reserve_amount": eligible_reserve_amount,
                "invested_amount": invested_amount,
                "goal_100k_remaining": goal_100k_remaining,
                "future_commitments_next_month": future_commitments_next_month,
            },
        )

    def replace_alert(
        self,
        *,
        reference_date: date,
        alert_type: str,
        severity: str,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        self.execute(
            "delete from gold.financial_alerts where reference_date = :reference_date and alert_type = :alert_type",
            {"reference_date": reference_date, "alert_type": alert_type},
        )
        self.execute(
            """
            insert into gold.financial_alerts (
                reference_date,
                alert_type,
                severity,
                message,
                payload
            )
            values (
                :reference_date,
                :alert_type,
                :severity,
                :message,
                cast(:payload as jsonb)
            )
            """,
            {
                "reference_date": reference_date,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "payload": _json(payload),
            },
        )
