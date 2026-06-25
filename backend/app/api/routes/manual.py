from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.repositories.manual_repository import ManualRepository
from app.schemas.manual import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategorizationRuleCreate,
    CategorizationRuleResponse,
    CategorizationRuleUpdate,
    CategorizePreviewRequest,
    CategorizePreviewResponse,
    GoalCreate,
    GoalResponse,
    GoalUpdate,
    CardCreate,
    CardInvoiceCreate,
    CardInvoiceResponse,
    CardInvoiceUpdate,
    CardResponse,
    CardTransactionCreate,
    CardTransactionResponse,
    CardUpdate,
    ManualInvestmentCreate,
    ManualInvestmentResponse,
    ManualInvestmentUpdate,
    ManualTransactionCreate,
    ManualTransactionResponse,
    ManualTransactionUpdate,
)

router = APIRouter(tags=["manual"])


def _not_found() -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")


@router.get("/manual/accounts", response_model=list[AccountResponse])
def list_accounts(session: Session = Depends(get_db_session)) -> list[AccountResponse]:
    return ManualRepository(session).list_accounts()


@router.post("/manual/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, session: Session = Depends(get_db_session)) -> AccountResponse:
    return ManualRepository(session).create_account(payload)


@router.patch("/manual/accounts/{account_id}", response_model=AccountResponse)
def update_account(account_id: UUID, payload: AccountUpdate, session: Session = Depends(get_db_session)) -> AccountResponse:
    result = ManualRepository(session).update_account(account_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/manual/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_account(account_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(session: Session = Depends(get_db_session)) -> list[CategoryResponse]:
    return ManualRepository(session).list_categories()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, session: Session = Depends(get_db_session)) -> CategoryResponse:
    return ManualRepository(session).create_category(payload)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: UUID, payload: CategoryUpdate, session: Session = Depends(get_db_session)) -> CategoryResponse:
    result = ManualRepository(session).update_category(category_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_category(category_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/categorization-rules", response_model=list[CategorizationRuleResponse])
def list_categorization_rules(session: Session = Depends(get_db_session)) -> list[CategorizationRuleResponse]:
    return ManualRepository(session).list_categorization_rules()


@router.post("/categorization-rules", response_model=CategorizationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_categorization_rule(
    payload: CategorizationRuleCreate,
    session: Session = Depends(get_db_session),
) -> CategorizationRuleResponse:
    return ManualRepository(session).create_categorization_rule(payload)


@router.patch("/categorization-rules/{rule_id}", response_model=CategorizationRuleResponse)
def update_categorization_rule(
    rule_id: UUID,
    payload: CategorizationRuleUpdate,
    session: Session = Depends(get_db_session),
) -> CategorizationRuleResponse:
    result = ManualRepository(session).update_categorization_rule(rule_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/categorization-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categorization_rule(rule_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_categorization_rule(rule_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/categorize/preview", response_model=CategorizePreviewResponse)
def categorize_preview(
    payload: CategorizePreviewRequest,
    session: Session = Depends(get_db_session),
) -> CategorizePreviewResponse:
    return ManualRepository(session).preview_category(payload)


@router.get("/manual/goals", response_model=list[GoalResponse])
def list_goals(session: Session = Depends(get_db_session)) -> list[GoalResponse]:
    return ManualRepository(session).list_goals()


@router.post("/manual/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, session: Session = Depends(get_db_session)) -> GoalResponse:
    return ManualRepository(session).create_goal(payload)


@router.patch("/manual/goals/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: UUID, payload: GoalUpdate, session: Session = Depends(get_db_session)) -> GoalResponse:
    result = ManualRepository(session).update_goal(goal_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/manual/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_goal(goal_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/manual/transactions", response_model=list[ManualTransactionResponse])
def list_manual_transactions(session: Session = Depends(get_db_session)) -> list[ManualTransactionResponse]:
    return ManualRepository(session).list_manual_transactions()


@router.post("/manual/transactions", response_model=ManualTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_manual_transaction(
    payload: ManualTransactionCreate,
    session: Session = Depends(get_db_session),
) -> ManualTransactionResponse:
    return ManualRepository(session).create_manual_transaction(payload)


@router.patch("/manual/transactions/{transaction_id}", response_model=ManualTransactionResponse)
def update_manual_transaction(
    transaction_id: UUID,
    payload: ManualTransactionUpdate,
    session: Session = Depends(get_db_session),
) -> ManualTransactionResponse:
    result = ManualRepository(session).update_manual_transaction(transaction_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/manual/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manual_transaction(transaction_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_manual_transaction(transaction_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/manual/investments", response_model=list[ManualInvestmentResponse])
def list_manual_investments(session: Session = Depends(get_db_session)) -> list[ManualInvestmentResponse]:
    return ManualRepository(session).list_manual_investments()


@router.post("/manual/investments", response_model=ManualInvestmentResponse, status_code=status.HTTP_201_CREATED)
def create_manual_investment(
    payload: ManualInvestmentCreate,
    session: Session = Depends(get_db_session),
) -> ManualInvestmentResponse:
    return ManualRepository(session).create_manual_investment(payload)


@router.patch("/manual/investments/{investment_id}", response_model=ManualInvestmentResponse)
def update_manual_investment(
    investment_id: UUID,
    payload: ManualInvestmentUpdate,
    session: Session = Depends(get_db_session),
) -> ManualInvestmentResponse:
    result = ManualRepository(session).update_manual_investment(investment_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/manual/investments/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manual_investment(investment_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_manual_investment(investment_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/cards", response_model=list[CardResponse])
def list_cards(session: Session = Depends(get_db_session)) -> list[CardResponse]:
    return ManualRepository(session).list_cards()


@router.post("/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(payload: CardCreate, session: Session = Depends(get_db_session)) -> CardResponse:
    return ManualRepository(session).create_card(payload)


@router.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: UUID, payload: CardUpdate, session: Session = Depends(get_db_session)) -> CardResponse:
    result = ManualRepository(session).update_card(card_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_card(card_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/card-invoices", response_model=list[CardInvoiceResponse])
def list_card_invoices(session: Session = Depends(get_db_session)) -> list[CardInvoiceResponse]:
    return ManualRepository(session).list_card_invoices()


@router.post("/card-invoices", response_model=CardInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_card_invoice(
    payload: CardInvoiceCreate,
    session: Session = Depends(get_db_session),
) -> CardInvoiceResponse:
    return ManualRepository(session).create_card_invoice(payload)


@router.patch("/card-invoices/{invoice_id}", response_model=CardInvoiceResponse)
def update_card_invoice(
    invoice_id: UUID,
    payload: CardInvoiceUpdate,
    session: Session = Depends(get_db_session),
) -> CardInvoiceResponse:
    result = ManualRepository(session).update_card_invoice(invoice_id, payload)
    if result is None:
        _not_found()
    return result


@router.delete("/card-invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card_invoice(invoice_id: UUID, session: Session = Depends(get_db_session)) -> Response:
    if not ManualRepository(session).delete_card_invoice(invoice_id):
        _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/card-invoices/{invoice_id}/transactions",
    response_model=CardTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_card_transaction(
    invoice_id: UUID,
    payload: CardTransactionCreate,
    session: Session = Depends(get_db_session),
) -> CardTransactionResponse:
    result = ManualRepository(session).create_card_transaction(invoice_id, payload)
    if result is None:
        _not_found()
    return result
