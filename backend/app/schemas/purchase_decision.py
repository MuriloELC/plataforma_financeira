from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PurchaseSimulationRequest(BaseModel):
    item: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    category_id: UUID | None = None
    payment_method: str
    installments: int = Field(default=1, ge=1)
    reason: str = Field(min_length=1)
    urgency: str
    is_planned: bool = False
    is_technology: bool = False
    justification: str | None = None
    decision_date: date | None = None


class PurchaseSimulationResponse(BaseModel):
    decision_id: UUID
    decision_date: date
    item: str
    amount: Decimal
    verdict: str
    reserve_impact_amount: Decimal
    contribution_impact_amount: Decimal
    goal_100k_delay_days: int
    future_commitment_impact: Decimal
    monthly_installment: Decimal
    requires_justification: bool
    explanation: str
    recommendation: str


class PurchaseDecisionHistoryItem(BaseModel):
    id: UUID
    decision_date: date
    item_name: str
    amount: Decimal
    category_id: UUID | None = None
    is_planned: bool
    is_technology: bool
    payment_method: str
    installments: int
    monthly_installment: Decimal | None = None
    urgency: str | None = None
    justification: str | None = None
    verdict: str | None = None
    reserve_impact_amount: Decimal | None = None
    contribution_impact_amount: Decimal | None = None
    goal_100k_delay_days: int | None = None
    future_commitment_impact: Decimal | None = None
    explanation: str | None = None
    created_at: datetime
