from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates

from budget_tracker.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    name_normalized: Mapped[str] = mapped_column(String, unique=True)
    color: Mapped[str] = mapped_column(String(7))

    @validates("name")
    def _sync_name_normalized(self, _key: str, value: str) -> str:
        self.name_normalized = value.casefold()
        return value
