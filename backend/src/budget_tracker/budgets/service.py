from sqlalchemy import select
from sqlalchemy.orm import Session

from budget_tracker.budgets.models import Budget
from budget_tracker.budgets.schemas import BudgetInput
from budget_tracker.categories.service import get_category
from budget_tracker.core.exceptions import NotFoundError
from budget_tracker.core.types import to_cents


def list_budgets(db: Session, month: str) -> list[Budget]:
    query = select(Budget).where(Budget.month == month).order_by(Budget.category_id)
    return list(db.scalars(query))


def set_budget(db: Session, month: str, category_id: int, data: BudgetInput) -> Budget:
    get_category(db, category_id)
    budget = _find_budget(db, month, category_id)
    if budget is None:
        budget = Budget(month=month, category_id=category_id)
        db.add(budget)
    budget.amount_cents = to_cents(data.amount)
    db.commit()
    return budget


def delete_budget(db: Session, month: str, category_id: int) -> None:
    budget = _find_budget(db, month, category_id)
    if budget is None:
        raise NotFoundError(f"Category {category_id} has no budget for {month}.")
    db.delete(budget)
    db.commit()


def _find_budget(db: Session, month: str, category_id: int) -> Budget | None:
    query = select(Budget).where(Budget.month == month, Budget.category_id == category_id)
    return db.scalar(query)
