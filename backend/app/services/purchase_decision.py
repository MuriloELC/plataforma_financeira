from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_CEILING
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.purchase_decision_repository import PurchaseDecisionRepository
from app.schemas.purchase_decision import (
    PurchaseDecisionHistoryItem,
    PurchaseSimulationRequest,
    PurchaseSimulationResponse,
)

VERDICT_BUY_NOW = "Comprar agora"
VERDICT_BUY_WITH_ADJUSTMENT = "Comprar com ajuste"
VERDICT_WAIT = "Esperar"
VERDICT_AVOID = "Evitar"


class PurchaseDecisionError(Exception):
    pass


class PurchaseDecisionService:
    def __init__(self, session: Session) -> None:
        self.repository = PurchaseDecisionRepository(session)

    def simulate(self, request: PurchaseSimulationRequest) -> PurchaseSimulationResponse:
        decision_date = request.decision_date or date.today()
        context = self.repository.latest_context(decision_date)
        if context is None:
            raise PurchaseDecisionError("Gold purchase decision context is not available. Run /gold/refresh first.")

        monthly_installment = _money(request.amount / Decimal(request.installments))
        immediate_impact = self._immediate_impact(request, monthly_installment)
        future_commitment_impact = monthly_installment if request.installments > 1 else Decimal("0.00")

        available = context["available_after_commitments"]
        if available is None:
            available = self.repository.current_cash_balance(decision_date) - (context["future_commitments_next_month"] or Decimal("0"))
        available_after_purchase = available - immediate_impact

        reserve_target = context["reserve_target"] or Decimal("0")
        reserve_available = context["eligible_reserve_amount"] or Decimal("0")
        reserve_after_purchase = reserve_available - immediate_impact
        reserve_impact = max(reserve_target - reserve_after_purchase, Decimal("0"))

        minimum_contribution = context["minimum_monthly_contribution"] or Decimal("300.00")
        contribution_impact = max(minimum_contribution - available_after_purchase, Decimal("0"))
        requires_justification = self._requires_justification(request, contribution_impact)
        provided_justification = bool((request.justification or "").strip())

        if requires_justification and not provided_justification:
            raise PurchaseDecisionError("Justificativa obrigatoria para esta decisao.")

        delay_days = self._delay_days(contribution_impact, request.amount, minimum_contribution)
        verdict = self._verdict(
            request=request,
            available_after_purchase=available_after_purchase,
            reserve_target=reserve_target,
            reserve_after_purchase=reserve_after_purchase,
            contribution_impact=contribution_impact,
            provided_justification=provided_justification,
        )
        explanation = self._explanation(
            verdict=verdict,
            reserve_impact=reserve_impact,
            contribution_impact=contribution_impact,
            future_commitment_impact=future_commitment_impact,
            delay_days=delay_days,
        )
        recommendation = self._recommendation(verdict)

        saved = self.repository.insert_decision(
            decision_date=decision_date,
            item_name=request.item,
            amount=request.amount,
            category_id=request.category_id,
            is_planned=request.is_planned,
            is_technology=request.is_technology,
            payment_method=request.payment_method,
            installments=request.installments,
            monthly_installment=monthly_installment,
            urgency=request.urgency,
            justification=request.justification or request.reason,
            verdict=verdict,
            reserve_impact_amount=_money(reserve_impact),
            contribution_impact_amount=_money(contribution_impact),
            goal_100k_delay_days=delay_days,
            future_commitment_impact=_money(future_commitment_impact),
            explanation=explanation,
        )

        return PurchaseSimulationResponse(
            decision_id=saved["id"],
            decision_date=saved["decision_date"],
            item=request.item,
            amount=request.amount,
            verdict=verdict,
            reserve_impact_amount=_money(reserve_impact),
            contribution_impact_amount=_money(contribution_impact),
            goal_100k_delay_days=delay_days,
            future_commitment_impact=_money(future_commitment_impact),
            monthly_installment=monthly_installment,
            requires_justification=requires_justification,
            explanation=explanation,
            recommendation=recommendation,
        )

    def list_history(self, limit: int) -> list[PurchaseDecisionHistoryItem]:
        return [PurchaseDecisionHistoryItem(**row) for row in self.repository.list_decisions(limit)]

    def _immediate_impact(self, request: PurchaseSimulationRequest, monthly_installment: Decimal) -> Decimal:
        method = request.payment_method.lower()
        if method in {"credit_card", "cartao", "cartao_credito", "credit"}:
            return monthly_installment
        return request.amount

    def _requires_justification(
        self,
        request: PurchaseSimulationRequest,
        contribution_impact: Decimal,
    ) -> bool:
        if request.is_technology and request.amount > Decimal("300"):
            return True
        if contribution_impact > 0:
            return True
        return False

    def _verdict(
        self,
        *,
        request: PurchaseSimulationRequest,
        available_after_purchase: Decimal,
        reserve_target: Decimal,
        reserve_after_purchase: Decimal,
        contribution_impact: Decimal,
        provided_justification: bool,
    ) -> str:
        urgency = request.urgency.lower()
        if available_after_purchase < 0:
            return VERDICT_AVOID
        if reserve_target > 0 and reserve_after_purchase < reserve_target * Decimal("0.5") and urgency not in {"alta", "high", "urgente"}:
            return VERDICT_AVOID
        if reserve_after_purchase < reserve_target:
            return VERDICT_WAIT if urgency not in {"alta", "high", "urgente"} else VERDICT_BUY_WITH_ADJUSTMENT
        if contribution_impact > 0:
            return VERDICT_BUY_WITH_ADJUSTMENT if provided_justification else VERDICT_WAIT
        if not request.is_planned and request.amount > Decimal("300"):
            return VERDICT_BUY_WITH_ADJUSTMENT if provided_justification else VERDICT_WAIT
        return VERDICT_BUY_NOW

    def _delay_days(self, contribution_impact: Decimal, amount: Decimal, minimum_contribution: Decimal) -> int:
        if contribution_impact > 0:
            return _ceil((contribution_impact / minimum_contribution) * Decimal("30"))
        if amount > minimum_contribution:
            return _ceil((amount / minimum_contribution) * Decimal("7"))
        return 0

    def _explanation(
        self,
        *,
        verdict: str,
        reserve_impact: Decimal,
        contribution_impact: Decimal,
        future_commitment_impact: Decimal,
        delay_days: int,
    ) -> str:
        parts = [f"Veredito: {verdict}."]
        if reserve_impact > 0:
            parts.append(f"A compra deixa a reserva abaixo do alvo em R$ {_money(reserve_impact)}.")
        if contribution_impact > 0:
            parts.append(f"A compra compromete R$ {_money(contribution_impact)} do aporte minimo.")
        if future_commitment_impact > 0:
            parts.append(f"Parcelas adicionam R$ {_money(future_commitment_impact)} aos compromissos futuros.")
        if delay_days > 0:
            parts.append(f"Atraso estimado na meta de R$ 100 mil: {delay_days} dias.")
        if len(parts) == 1:
            parts.append("Impactos principais estao dentro dos limites atuais.")
        return " ".join(parts)

    def _recommendation(self, verdict: str) -> str:
        if verdict == VERDICT_BUY_NOW:
            return "Pode seguir sem ajuste financeiro relevante."
        if verdict == VERDICT_BUY_WITH_ADJUSTMENT:
            return "Comprar somente mantendo compensacao explicita no mes."
        if verdict == VERDICT_WAIT:
            return "Aguardar recompor reserva ou aporte antes de comprar."
        return "Evitar a compra nas condicoes atuais."


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _ceil(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))
