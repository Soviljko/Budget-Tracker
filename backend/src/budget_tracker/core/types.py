from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints

MAX_AMOUNT = Decimal("1000000.00")

Amount = Annotated[
    Decimal,
    Field(gt=0, le=MAX_AMOUNT, decimal_places=2, examples=["12.50"]),
]

CategoryName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
]

HexColor = Annotated[
    str,
    StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$", to_upper=True),
]

Month = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
]


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


Description = Annotated[
    str | None,
    Field(max_length=200),
    AfterValidator(_blank_to_none),
]


def to_cents(amount: Decimal) -> int:
    return int(amount * 100)


def from_cents(cents: int) -> Decimal:
    return Decimal(cents).scaleb(-2)
