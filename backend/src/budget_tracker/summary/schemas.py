from decimal import Decimal

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category_id: int
    name: str
    spent: Decimal
    budget: Decimal | None
    left: Decimal | None


class MonthlySummary(BaseModel):
    month: str
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    categories: list[CategorySummary]
