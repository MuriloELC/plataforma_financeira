from datetime import date, datetime
from decimal import Decimal
from typing import Any
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
