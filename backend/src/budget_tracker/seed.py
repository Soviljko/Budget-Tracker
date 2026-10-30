"""Data command: fill the database with sample data, or generate a large CSV for the import.

Usage (from the backend folder):
    uv run python -m budget_tracker.seed                  # add sample data
    uv run python -m budget_tracker.seed --reset          # delete everything, then add sample data
    uv run python -m budget_tracker.seed --csv data/transactions.csv --rows 1000000
"""

import argparse
import csv
import datetime as dt
import random
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from budget_tracker.budgets.models import Budget
from budget_tracker.categories.models import Category
from budget_tracker.core.database import Base, SessionLocal, engine
from budget_tracker.transactions.models import Transaction, TransactionType

# Category name -> (color, monthly budget in euros or None)
CATEGORIES: dict[str, tuple[str, int | None]] = {
    "Salary": ("#2E7D32", None),
    "Rent": ("#6D4C41", 600),
    "Groceries": ("#F9A825", 300),
    "Eating out": ("#EF6C00", 100),
    "Transport": ("#1565C0", 60),
    "Bills": ("#5E35B1", 150),
    "Entertainment": ("#AD1457", 80),
    "Other": ("#546E7A", None),
}

# Category name -> (possible descriptions, min amount, max amount, transactions per month)
EXPENSES: dict[str, tuple[list[str], int, int, int]] = {
    "Groceries": (["Supermarket", "Local market", "Bakery"], 5, 70, 8),
    "Eating out": (["Lunch", "Dinner with friends", "Coffee"], 3, 40, 6),
    "Transport": (["Bus ticket", "Taxi", "Fuel"], 2, 45, 4),
    "Bills": (["Electricity", "Internet", "Phone"], 20, 60, 3),
    "Entertainment": (["Cinema", "Concert", "Streaming subscription"], 8, 50, 3),
}

MONTHS_OF_DATA = 3
SALARY = 2000
RENT = 600


def seed_database(db: Session, rng: random.Random, today: dt.date) -> None:
    categories = {
        name: Category(name=name, color=color) for name, (color, _budget) in CATEGORIES.items()
    }
    db.add_all(categories.values())
    db.flush()  # assigns ids to the categories

    for months_back in range(MONTHS_OF_DATA):
        first_day = _first_day_of_month(today, months_back)
        last_day = today if months_back == 0 else _last_day_of_month(first_day)
        month = first_day.strftime("%Y-%m")

        db.add(
            _transaction(
                TransactionType.INCOME, SALARY, first_day, "Monthly salary", categories["Salary"]
            )
        )
        db.add(
            _transaction(
                TransactionType.EXPENSE, RENT, first_day, "Apartment rent", categories["Rent"]
            )
        )

        for name, (descriptions, low, high, per_month) in EXPENSES.items():
            for _ in range(per_month):
                day = first_day + dt.timedelta(days=rng.randrange((last_day - first_day).days + 1))
                amount = round(rng.uniform(low, high), 2)
                description = rng.choice(descriptions)
                db.add(
                    _transaction(
                        TransactionType.EXPENSE, amount, day, description, categories[name]
                    )
                )

        for name, (_color, budget) in CATEGORIES.items():
            if budget is not None:
                db.add(
                    Budget(category_id=categories[name].id, month=month, amount_cents=budget * 100)
                )

    db.commit()


def write_csv(path: Path, rows: int, rng: random.Random) -> None:
    """Write a CSV in the import format. Every 10,000th row is invalid on purpose."""
    path.parent.mkdir(parents=True, exist_ok=True)
    expense_names = list(EXPENSES)
    start = dt.date(2026, 1, 1)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["type", "amount", "date", "description", "category"])
        for row in range(1, rows + 1):
            day = (start + dt.timedelta(days=row % 300)).isoformat()
            if row % 10_000 == 0:
                writer.writerow(["expense", "-5.00", day, "Invalid amount", "Groceries"])
            elif row % 10_000 == 5_000:
                writer.writerow(["expense", "5.00", day, "Unknown category", "Holidays"])
            elif row % 50 == 0:
                writer.writerow(["income", "100.00", day, "", "Other"])
            else:
                name = rng.choice(expense_names)
                descriptions, low, high, _per_month = EXPENSES[name]
                amount = f"{rng.uniform(low, high):.2f}"
                writer.writerow(["expense", amount, day, rng.choice(descriptions), name])


def _transaction(
    type_: TransactionType, amount: float, date: dt.date, description: str, category: Category
) -> Transaction:
    return Transaction(
        type=type_,
        amount_cents=round(amount * 100),
        date=date,
        description=description,
        category_id=category.id,
    )


def _first_day_of_month(today: dt.date, months_back: int) -> dt.date:
    month_index = today.year * 12 + (today.month - 1) - months_back
    return dt.date(month_index // 12, month_index % 12 + 1, 1)


def _last_day_of_month(first_day: dt.date) -> dt.date:
    return _first_day_of_month(first_day, -1) - dt.timedelta(days=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reset", action="store_true", help="delete all data before seeding")
    parser.add_argument("--csv", type=Path, help="write a CSV file for the import instead")
    parser.add_argument("--rows", type=int, default=1_000_000, help="number of CSV rows")
    args = parser.parse_args()
    rng = random.Random(42)  # fixed seed: the same data every time

    if args.csv:
        write_csv(args.csv, args.rows, rng)
        print(f"Wrote {args.rows:,} rows to {args.csv}.")
        print("Its categories exist after running the seed command without --csv.")
        return

    if args.reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Category)):
            print("The database already has data. Run with --reset to start over.")
            return
        seed_database(db, rng, dt.date.today())
        transactions = db.scalar(select(func.count()).select_from(Transaction))
        print(
            f"Added {len(CATEGORIES)} categories and {transactions} transactions "
            f"for the last {MONTHS_OF_DATA} months, with budgets."
        )


if __name__ == "__main__":
    main()
