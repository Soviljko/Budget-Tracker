import datetime as dt
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field, model_validator

from budget_tracker.core.types import Amount, CategoryName, Description, from_cents
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


class TransactionQuery(BaseModel):
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    category_id: int | None = None
    type: TransactionType | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def _check_date_range(self) -> Self:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to.")
        return self


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int


class CsvRow(BaseModel):
    """One CSV row. Same rules as TransactionInput, but the category is given by name."""

    type: TransactionType
    amount: Amount
    date: dt.date
    description: Description = None
    category: CategoryName


class RowError(BaseModel):
    row: int
    errors: list[str]


class ImportResult(BaseModel):
    imported: int
    failed: int
    errors: list[RowError]
