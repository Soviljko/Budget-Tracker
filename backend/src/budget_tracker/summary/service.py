import calendar
import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from budget_tracker.budgets.models import Budget
from budget_tracker.categories.models import Category
from budget_tracker.core.types import from_cents
from budget_tracker.summary.schemas import CategorySummary, MonthlySummary
from budget_tracker.transactions.models import Transaction, TransactionType


def get_monthly_summary(db: Session, month: str) -> MonthlySummary:
    first_day, last_day = _month_bounds(month)
    in_month = Transaction.date.between(first_day, last_day)

    totals = dict(
        db.execute(
            select(Transaction.type, func.sum(Transaction.amount_cents))
            .where(in_month)
            .group_by(Transaction.type)
        ).all()
    )

    spent = dict(
        db.execute(
            select(Transaction.category_id, func.sum(Transaction.amount_cents))
            .where(in_month, Transaction.type == TransactionType.EXPENSE)
            .group_by(Transaction.category_id)
        ).all()
    )

    budgets = dict(
        db.execute(
            select(Budget.category_id, Budget.amount_cents).where(Budget.month == month)
        ).all()
    )

    category_ids = list(spent.keys() | budgets.keys())
    categories = db.scalars(select(Category).where(Category.id.in_(category_ids)))
    categories = sorted(categories, key=lambda c: (-spent.get(c.id, 0), c.name_normalized))

    income = totals.get(TransactionType.INCOME, 0)
    expense = totals.get(TransactionType.EXPENSE, 0)

    return MonthlySummary(
        month=month,
        total_income=from_cents(income),
        total_expense=from_cents(expense),
        balance=from_cents(income - expense),
        categories=[
            _category_summary(category, spent.get(category.id, 0), budgets.get(category.id))
            for category in categories
        ],
    )


def _category_summary(
    category: Category, spent_cents: int, budget_cents: int | None
) -> CategorySummary:
    has_budget = budget_cents is not None
    return CategorySummary(
        category_id=category.id,
        name=category.name,
        spent=from_cents(spent_cents),
        budget=from_cents(budget_cents) if has_budget else None,
        left=from_cents(budget_cents - spent_cents) if has_budget else None,
    )


def _month_bounds(month: str) -> tuple[dt.date, dt.date]:
    year, month_number = map(int, month.split("-"))
    last_day = calendar.monthrange(year, month_number)[1]
    return dt.date(year, month_number, 1), dt.date(year, month_number, last_day)
