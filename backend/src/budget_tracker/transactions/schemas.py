import datetime as dt
from decimal import Decimal
from typing import Self

from pydantic import BaseModel

from budget_tracker.core.types import Amount, Description, from_cents
from budget_tracker.transactions.models import Transaction, TransactionType


class TransactionInput(BaseModel):
    type: TransactionType
    amount: Amount
    date: dt.date
    description: Description = None
    category_id: int


class TransactionRead(BaseModel):
    id: int
    type: TransactionType
    amount: Decimal
    date: dt.date
    description: str | None
    category_id: int

    @classmethod
    def from_model(cls, transaction: Transaction) -> Self:
        return cls(
            id=transaction.id,
            type=transaction.type,
            amount=from_cents(transaction.amount_cents),
            date=transaction.date,
            description=transaction.description,
            category_id=transaction.category_id,
        )
