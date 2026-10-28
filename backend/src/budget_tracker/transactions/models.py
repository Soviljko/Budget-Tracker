import datetime as dt
from enum import StrEnum

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, validates

from budget_tracker.core.database import Base


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_date_id", "date", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TransactionType]
    amount_cents: Mapped[int]
    date: Mapped[dt.date]
    description: Mapped[str | None] = mapped_column(String(200))
    description_normalized: Mapped[str | None]
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )

    @validates("description")
    def _sync_description_normalized(self, _key: str, value: str | None) -> str | None:
        self.description_normalized = value.casefold() if value else None
        return value
