from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal, ROUND_CEILING
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.gold_repository import GoldRepository
from app.schemas.gold import GoldRefreshResponse

TARGET_PASSIVE_INCOME = Decimal("5000.00")
TARGET_INVESTED = Decimal("100000.00")
MINIMUM_MONTHLY_CONTRIBUTION = Decimal("300.00")


class GoldService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = GoldRepository(session)

    def refresh(self, reference_date: date) -> GoldRefreshResponse:
        reference_month = _month_start(reference_date)
        counts: Counter[str] = Counter()

        passive = self._refresh_passive_income(reference_month)
        counts["passive_income_monthly"] = 1

        invested = self._investment_total(reference_date)
        avg_contribution = self._average_monthly_contribution(reference_month)
        remaining = max(TARGET_INVESTED - invested, Decimal("0"))
        estimated_months = _ceil_decimal(remaining / avg_contribution) if avg_contribution and avg_contribution > 0 else None
        self.repository.replace_goal_100k(
            reference_date=reference_date,
            invested_amount=invested,
            remaining_amount=remaining,
            progress_pct=_pct(invested, TARGET_INVESTED),
            avg_monthly_contribution=avg_contribution,
            estimated_months_to_goal=estimated_months,
        )
        counts["goal_100k_progress"] = 1

        reserve = self._refresh_reserve(reference_date)
        counts["reserve_status"] = 1

        allocations = self._allocation(reference_date)
        self.repository.replace_allocation(reference_date=reference_date, allocations=allocations)
        counts["portfolio_allocation"] = len(allocations)

        commitments = self._future_commitments(reference_month)
        self.repository.replace_future_commitments(month_start=reference_month, commitments=commitments)
        counts["future_commitments"] = len(commitments)

        next_month = _add_months(reference_month, 1)
        future_next_month = sum(
            item["amount"] for item in commitments if item["due_month"] == next_month
        )
        self.repository.replace_purchase_context(
            reference_date=reference_date,
            minimum_monthly_contribution=MINIMUM_MONTHLY_CONTRIBUTION,
            reserve_target=reserve["reserve_target"],
            eligible_reserve_amount=reserve["eligible_reserve_amount"],
            invested_amount=invested,
            goal_100k_remaining=remaining,
            future_commitments_next_month=future_next_month,
        )
        counts["purchase_decision_context"] = 1

        contribution_this_month = self._monthly_contribution(reference_month)
        severity = "info" if contribution_this_month >= MINIMUM_MONTHLY_CONTRIBUTION else "warning"
        message = "Aporte minimo mensal cumprido." if severity == "info" else "Aporte minimo mensal abaixo do piso."
        self.repository.replace_alert(
            reference_date=reference_date,
            alert_type="minimum_contribution",
            severity=severity,
            message=message,
            payload={
                "minimum_monthly_contribution": MINIMUM_MONTHLY_CONTRIBUTION,
                "actual_contribution": contribution_this_month,
            },
        )
        counts["financial_alerts"] = 1

        self.session.commit()
        return GoldRefreshResponse(reference_date=reference_date, refreshed=dict(counts))

    def list_table(self, table_name: str, limit: int = 50) -> list[dict[str, Any]]:
        allowed = {
            "passive_income_monthly",
            "goal_100k_progress",
            "reserve_status",
            "portfolio_allocation",
            "future_commitments",
            "purchase_decision_context",
            "financial_alerts",
        }
        if table_name not in allowed:
            raise ValueError("Invalid Gold table.")
        return self.repository.rows(
            f"select * from gold.{table_name} order by created_at desc, id desc limit :limit",
            {"limit": limit},
        )

    def _refresh_passive_income(self, reference_month: date) -> dict[str, Decimal]:
        months = [_add_months(reference_month, offset) for offset in range(-11, 1)]
        start = months[0]
        end = _add_months(reference_month, 1)
        rows = self.repository.rows(
            """
            select date_trunc('month', coalesce(payment_date, reference_date))::date as month,
                   sum(coalesce(net_amount, gross_amount, 0)) as received_amount
            from silver.investment_income
            where coalesce(payment_date, reference_date) >= :start
              and coalesce(payment_date, reference_date) < :end
              and is_received = true
            group by 1
            """,
            {"start": start, "end": end},
        )
        by_month = {row["month"]: row["received_amount"] or Decimal("0") for row in rows}
        values = [by_month.get(month, Decimal("0")) for month in months]
        received = values[-1]
        avg3 = sum(values[-3:], Decimal("0")) / Decimal("3")
        avg12 = sum(values, Decimal("0")) / Decimal("12")

        accrued = self.repository.scalar(
            """
            select coalesce(sum(coalesce(net_amount, gross_amount, 0)), 0)
            from silver.investment_income
            where coalesce(payment_date, reference_date) >= :start
              and coalesce(payment_date, reference_date) < :end
              and is_accrued = true
            """,
            {"start": reference_month, "end": end},
        )
        self.repository.replace_passive_income(
            month=reference_month,
            received_amount=received,
            accrued_amount=accrued,
            avg_3m_received=avg3,
            avg_12m_received=avg12,
            progress_pct=_pct(received, TARGET_PASSIVE_INCOME),
        )
        return {"received_amount": received, "avg_3m_received": avg3, "avg_12m_received": avg12}

    def _investment_total(self, reference_date: date) -> Decimal:
        listed = self.repository.scalar(
            """
            with latest as (
                select distinct on (asset_id)
                    asset_id,
                    coalesce(net_value, gross_value, market_value, 0) as amount
                from silver.investment_positions
                where reference_date <= :reference_date
                order by asset_id, reference_date desc, created_at desc
            )
            select coalesce(sum(amount), 0) from latest
            """,
            {"reference_date": reference_date},
        )
        manual = self.repository.scalar(
            """
            with latest as (
                select distinct on (coalesce(asset_id, id), institution, product_name)
                    coalesce(net_value, gross_value, 0) as amount
                from silver.manual_investment_positions
                where reference_date <= :reference_date
                order by coalesce(asset_id, id), institution, product_name, reference_date desc, created_at desc
            )
            select coalesce(sum(amount), 0) from latest
            """,
            {"reference_date": reference_date},
        )
        pension = self.repository.scalar(
            """
            with latest as (
                select distinct on (institution, plan_name)
                    coalesce(vested_balance, total_balance, 0) as amount
                from silver.pension_positions
                where reference_date <= :reference_date
                order by institution, plan_name, reference_date desc, created_at desc
            )
            select coalesce(sum(amount), 0) from latest
            """,
            {"reference_date": reference_date},
        )
        return listed + manual + pension

    def _refresh_reserve(self, reference_date: date) -> dict[str, Decimal | str]:
        reference_month = _month_start(reference_date)
        months = [_add_months(reference_month, offset) for offset in range(-2, 1)]
        cash_rows = self.repository.rows(
            """
            select date_trunc('month', transaction_date)::date as month,
                   sum(abs(amount)) as amount
            from silver.cash_transactions
            where transaction_date >= :start
              and transaction_date < :end
              and amount < 0
              and is_transfer = false
              and transaction_type <> 'card_payment'
            group by 1
            """,
            {"start": months[0], "end": _add_months(reference_month, 1)},
        )
        card_rows = self.repository.rows(
            """
            select date_trunc('month', purchase_date)::date as month,
                   sum(amount) as amount
            from silver.card_transactions
            where purchase_date >= :start
              and purchase_date < :end
            group by 1
            """,
            {"start": months[0], "end": _add_months(reference_month, 1)},
        )
        by_month = {month: Decimal("0") for month in months}
        for row in [*cash_rows, *card_rows]:
            by_month[row["month"]] = by_month.get(row["month"], Decimal("0")) + (row["amount"] or Decimal("0"))
        avg_expenses = sum(by_month.values(), Decimal("0")) / Decimal("3")
        target = avg_expenses * Decimal("6")
        eligible = self._eligible_reserve_amount(reference_date)
        gap = eligible - target
        status = "complete" if gap >= 0 and target > 0 else "building" if eligible > 0 else "empty"
        self.repository.replace_reserve_status(
            reference_date=reference_date,
            avg_monthly_expenses_3m=avg_expenses,
            reserve_target=target,
            eligible_reserve_amount=eligible,
            gap_amount=gap,
            status=status,
        )
        return {
            "avg_monthly_expenses_3m": avg_expenses,
            "reserve_target": target,
            "eligible_reserve_amount": eligible,
            "gap_amount": gap,
            "status": status,
        }

    def _eligible_reserve_amount(self, reference_date: date) -> Decimal:
        listed = self.repository.scalar(
            """
            with latest as (
                select distinct on (asset_id)
                    coalesce(net_value, gross_value, market_value, 0) as amount,
                    counts_as_reserve
                from silver.investment_positions
                where reference_date <= :reference_date
                order by asset_id, reference_date desc, created_at desc
            )
            select coalesce(sum(amount), 0) from latest where counts_as_reserve = true
            """,
            {"reference_date": reference_date},
        )
        manual = self.repository.scalar(
            """
            with latest as (
                select distinct on (coalesce(asset_id, id), institution, product_name)
                    coalesce(net_value, gross_value, 0) as amount,
                    counts_as_reserve
                from silver.manual_investment_positions
                where reference_date <= :reference_date
                order by coalesce(asset_id, id), institution, product_name, reference_date desc, created_at desc
            )
            select coalesce(sum(amount), 0) from latest where counts_as_reserve = true
            """,
            {"reference_date": reference_date},
        )
        return listed + manual

    def _allocation(self, reference_date: date) -> list[dict[str, Any]]:
        rows = self.repository.rows(
            """
            with latest_positions as (
                select distinct on (p.asset_id)
                    a.asset_class,
                    coalesce(p.net_value, p.gross_value, p.market_value, 0) as amount,
                    p.counts_as_reserve
                from silver.investment_positions p
                join silver.investment_assets a on a.id = p.asset_id
                where p.reference_date <= :reference_date
                order by p.asset_id, p.reference_date desc, p.created_at desc
            ),
            latest_manual as (
                select distinct on (coalesce(asset_id, id), institution, product_name)
                    asset_class,
                    coalesce(net_value, gross_value, 0) as amount,
                    counts_as_reserve
                from silver.manual_investment_positions
                where reference_date <= :reference_date
                order by coalesce(asset_id, id), institution, product_name, reference_date desc, created_at desc
            )
            select asset_class, counts_as_reserve, sum(amount) as amount
            from (
                select * from latest_positions
                union all
                select * from latest_manual
            ) positions
            group by asset_class, counts_as_reserve
            """,
            {"reference_date": reference_date},
        )
        total = sum((row["amount"] or Decimal("0")) for row in rows)
        if total <= 0:
            return []
        return [
            {
                "asset_class": row["asset_class"],
                "amount": row["amount"],
                "allocation_pct": _pct(row["amount"], total),
                "counts_as_reserve": row["counts_as_reserve"],
            }
            for row in rows
        ]

    def _future_commitments(self, month_start: date) -> list[dict[str, Any]]:
        return self.repository.rows(
            """
            select
                i.due_month,
                'card_installment' as source,
                t.description_raw as description,
                i.installment_amount as amount,
                'installment' as commitment_type
            from silver.installments i
            join silver.card_transactions t on t.id = i.card_transaction_id
            where i.due_month >= :month_start
            order by i.due_month, t.description_raw
            """,
            {"month_start": month_start},
        )

    def _monthly_contribution(self, reference_month: date) -> Decimal:
        return self.repository.scalar(
            """
            select coalesce(sum(abs(amount)), 0)
            from silver.cash_transactions
            where transaction_date >= :start
              and transaction_date < :end
              and amount < 0
              and transaction_type in ('investment_transfer', 'investment_contribution')
            """,
            {"start": reference_month, "end": _add_months(reference_month, 1)},
        )

    def _average_monthly_contribution(self, reference_month: date) -> Decimal:
        start = _add_months(reference_month, -2)
        total = self.repository.scalar(
            """
            select coalesce(sum(abs(amount)), 0)
            from silver.cash_transactions
            where transaction_date >= :start
              and transaction_date < :end
              and amount < 0
              and transaction_type in ('investment_transfer', 'investment_contribution')
            """,
            {"start": start, "end": _add_months(reference_month, 1)},
        )
        return total / Decimal("3")


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _pct(value: Decimal, target: Decimal) -> Decimal:
    if target <= 0:
        return Decimal("0")
    return (value / target) * Decimal("100")


def _ceil_decimal(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))
