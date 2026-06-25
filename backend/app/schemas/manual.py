from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    institution: str
    account_name: str
    account_type: str


class AccountUpdate(BaseModel):
    institution: str | None = None
    account_name: str | None = None
    account_type: str | None = None
    is_active: bool | None = None


class AccountResponse(AccountCreate):
    id: UUID
    is_active: bool = True
    created_at: datetime


class CategoryCreate(BaseModel):
    name: str
    type: str
    parent_id: UUID | None = None
    is_system: bool = False


class CategoryUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    parent_id: UUID | None = None
    is_system: bool | None = None


class CategoryResponse(CategoryCreate):
    id: UUID
    created_at: datetime


class CategorizationRuleCreate(BaseModel):
    pattern: str = Field(min_length=1)
    category_id: UUID
    match_type: Literal["contains", "exact", "startswith"] = "contains"
    transaction_type: str | None = None
    priority: int = Field(default=100, ge=0)
    confidence_score: Decimal = Field(default=Decimal("0.8000"), ge=0, le=1)
    is_active: bool = True


class CategorizationRuleUpdate(BaseModel):
    pattern: str | None = Field(default=None, min_length=1)
    category_id: UUID | None = None
    match_type: Literal["contains", "exact", "startswith"] | None = None
    transaction_type: str | None = None
    priority: int | None = Field(default=None, ge=0)
    confidence_score: Decimal | None = Field(default=None, ge=0, le=1)
    is_active: bool | None = None


class CategorizationRuleResponse(CategorizationRuleCreate):
    id: UUID
    category_name: str | None = None
    created_at: datetime
    updated_at: datetime


class CategorizePreviewRequest(BaseModel):
    description: str = Field(min_length=1)
    transaction_type: str | None = None


class CategorizePreviewResponse(BaseModel):
    description: str
    transaction_type: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None
    matched_rule_id: UUID | None = None
    confidence_score: Decimal = Decimal("0.0000")
    needs_review: bool = True


class GoalCreate(BaseModel):
    name: str
    goal_type: str
    target_amount: Decimal | None = None
    target_date: date | None = None
    current_amount: Decimal = Decimal("0")
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class GoalUpdate(BaseModel):
    name: str | None = None
    goal_type: str | None = None
    target_amount: Decimal | None = None
    target_date: date | None = None
    current_amount: Decimal | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class GoalResponse(GoalCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ManualTransactionCreate(BaseModel):
    account_id: UUID
    transaction_date: date
    description_raw: str
    amount: Decimal
    category_id: UUID | None = None
    transaction_type: str = "manual"
    is_transfer: bool = False
    is_recurring: bool = False
    notes: str | None = None


class ManualTransactionUpdate(BaseModel):
    transaction_date: date | None = None
    description_raw: str | None = None
    amount: Decimal | None = None
    category_id: UUID | None = None
    transaction_type: str | None = None
    is_transfer: bool | None = None
    is_recurring: bool | None = None
    notes: str | None = None


class ManualTransactionResponse(ManualTransactionCreate):
    id: UUID
    direction: str
    created_at: datetime


class ManualInvestmentCreate(BaseModel):
    institution: str
    product_name: str
    asset_class: str
    reference_date: date
    gross_value: Decimal
    net_value: Decimal | None = None
    liquidity: str | None = None
    maturity_date: date | None = None
    rate_description: str | None = None
    counts_as_reserve: bool = False
    notes: str | None = None


class ManualInvestmentUpdate(BaseModel):
    institution: str | None = None
    product_name: str | None = None
    asset_class: str | None = None
    reference_date: date | None = None
    gross_value: Decimal | None = None
    net_value: Decimal | None = None
    liquidity: str | None = None
    maturity_date: date | None = None
    rate_description: str | None = None
    counts_as_reserve: bool | None = None
    notes: str | None = None


class ManualInvestmentResponse(ManualInvestmentCreate):
    id: UUID
    asset_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class CardCreate(BaseModel):
    institution: str
    card_name: str
    brand: str | None = None
    last_four_digits: str | None = None
    credit_limit: Decimal | None = None


class CardUpdate(BaseModel):
    institution: str | None = None
    card_name: str | None = None
    brand: str | None = None
    last_four_digits: str | None = None
    credit_limit: Decimal | None = None
    is_active: bool | None = None


class CardResponse(CardCreate):
    id: UUID
    is_active: bool = True
    created_at: datetime


class CardInvoiceCreate(BaseModel):
    card_id: UUID
    reference_month: date
    closing_date: date | None = None
    due_date: date | None = None
    total_amount: Decimal = Decimal("0")
    minimum_payment: Decimal | None = None
    credit_limit: Decimal | None = None
    used_limit: Decimal | None = None
    available_limit: Decimal | None = None
    next_invoice_committed_amount: Decimal | None = None
    future_debt_total: Decimal | None = None
    status: str = "open"


class CardInvoiceUpdate(BaseModel):
    reference_month: date | None = None
    closing_date: date | None = None
    due_date: date | None = None
    total_amount: Decimal | None = None
    minimum_payment: Decimal | None = None
    credit_limit: Decimal | None = None
    used_limit: Decimal | None = None
    available_limit: Decimal | None = None
    next_invoice_committed_amount: Decimal | None = None
    future_debt_total: Decimal | None = None
    status: str | None = None


class CardInvoiceResponse(CardInvoiceCreate):
    id: UUID
    created_at: datetime


class CardTransactionCreate(BaseModel):
    purchase_date: date
    description_raw: str
    amount: Decimal
    category_id: UUID | None = None
    installment_number: int = Field(default=1, ge=1)
    installment_total: int = Field(default=1, ge=1)


class CardTransactionResponse(CardTransactionCreate):
    id: UUID
    invoice_id: UUID
    card_id: UUID
    is_installment: bool
    created_at: datetime
