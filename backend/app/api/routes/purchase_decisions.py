from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.purchase_decision import (
    PurchaseDecisionHistoryItem,
    PurchaseSimulationRequest,
    PurchaseSimulationResponse,
)
from app.services.purchase_decision import PurchaseDecisionError, PurchaseDecisionService

router = APIRouter(tags=["purchase-decisions"])


@router.post("/purchase-decisions/simulate", response_model=PurchaseSimulationResponse)
def simulate_purchase_decision(
    payload: PurchaseSimulationRequest,
    session: Session = Depends(get_db_session),
) -> PurchaseSimulationResponse:
    try:
        return PurchaseDecisionService(session).simulate(payload)
    except PurchaseDecisionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/purchase-decisions", response_model=list[PurchaseDecisionHistoryItem])
def list_purchase_decisions(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[PurchaseDecisionHistoryItem]:
    return PurchaseDecisionService(session).list_history(limit=limit)
