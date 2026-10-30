from fastapi import APIRouter, status

from budget_tracker.budgets import service
from budget_tracker.budgets.schemas import BudgetInput, BudgetRead
from budget_tracker.core.database import DbSession
from budget_tracker.core.exceptions import error_responses
from budget_tracker.core.types import Id, Month

router = APIRouter(prefix="/budgets", tags=["budgets"], responses=error_responses(404, 422))


@router.get("")
def list_budgets(month: Month, db: DbSession) -> list[BudgetRead]:
    return [BudgetRead.from_model(b) for b in service.list_budgets(db, month)]


@router.put("/{month}/{category_id}")
def set_budget(month: Month, category_id: Id, data: BudgetInput, db: DbSession) -> BudgetRead:
    return BudgetRead.from_model(service.set_budget(db, month, category_id, data))


@router.delete("/{month}/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(month: Month, category_id: Id, db: DbSession) -> None:
    service.delete_budget(db, month, category_id)
