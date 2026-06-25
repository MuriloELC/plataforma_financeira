from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.gold import GoldRefreshResponse
from app.services.gold import GoldService

router = APIRouter(prefix="/gold", tags=["gold"])


@router.post("/refresh", response_model=GoldRefreshResponse)
def refresh_gold(
    reference_date: date = Query(...),
    session: Session = Depends(get_db_session),
) -> GoldRefreshResponse:
    return GoldService(session).refresh(reference_date)


@router.get("/passive-income")
def passive_income(limit: int = Query(default=12, ge=1, le=120), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("passive_income_monthly", limit=limit)


@router.get("/goal-100k")
def goal_100k(limit: int = Query(default=12, ge=1, le=120), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("goal_100k_progress", limit=limit)


@router.get("/reserve")
def reserve(limit: int = Query(default=12, ge=1, le=120), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("reserve_status", limit=limit)


@router.get("/allocation")
def allocation(limit: int = Query(default=50, ge=1, le=200), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("portfolio_allocation", limit=limit)


@router.get("/future-commitments")
def future_commitments(limit: int = Query(default=50, ge=1, le=200), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("future_commitments", limit=limit)


@router.get("/decision-context")
def decision_context(limit: int = Query(default=12, ge=1, le=120), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("purchase_decision_context", limit=limit)


@router.get("/alerts")
def alerts(limit: int = Query(default=50, ge=1, le=200), session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    return GoldService(session).list_table("financial_alerts", limit=limit)
