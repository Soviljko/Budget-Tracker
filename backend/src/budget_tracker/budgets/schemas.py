from decimal import Decimal
from typing import Self

from pydantic import BaseModel

from budget_tracker.budgets.models import Budget
from budget_tracker.core.types import Amount, from_cents


class BudgetInput(BaseModel):
    amount: Amount


class BudgetRead(BaseModel):
    id: int
    category_id: int
    month: str
    amount: Decimal

    @classmethod
    def from_model(cls, budget: Budget) -> Self:
        return cls(
            id=budget.id,
            category_id=budget.category_id,
            month=budget.month,
            amount=from_cents(budget.amount_cents),
        )
