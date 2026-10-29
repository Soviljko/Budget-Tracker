from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from budget_tracker.core.types import Amount, from_cents, to_cents


class AmountModel(BaseModel):
    amount: Amount


@pytest.mark.parametrize("value", ["0.01", "12.5", "1000000.00"])
def test_amount_accepts_valid_values(value: str) -> None:
    assert AmountModel(amount=value).amount == Decimal(value)


@pytest.mark.parametrize("value", ["0", "-5", "12.345", "1000000.01", "abc"])
def test_amount_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValidationError):
        AmountModel(amount=value)


def test_amount_is_converted_to_cents_and_back() -> None:
    assert to_cents(Decimal("12.50")) == 1250
    assert str(from_cents(1250)) == "12.50"
    assert str(from_cents(5)) == "0.05"
