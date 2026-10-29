from fastapi import APIRouter, status

from budget_tracker.budgets import service
from budget_tracker.budgets.schemas import BudgetInput, BudgetRead
from budget_tracker.core.database import DbSession
from budget_tracker.core.types import Month

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("")
def list_budgets(month: Month, db: DbSession) -> list[BudgetRead]:
    return [BudgetRead.from_model(b) for b in service.list_budgets(db, month)]


@router.put("/{month}/{category_id}")
def set_budget(month: Month, category_id: int, data: BudgetInput, db: DbSession) -> BudgetRead:
    return BudgetRead.from_model(service.set_budget(db, month, category_id, data))


@router.delete("/{month}/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(month: Month, category_id: int, db: DbSession) -> None:
    service.delete_budget(db, month, category_id)
