import csv
import io
from collections.abc import Iterator
from typing import BinaryIO

from pydantic import ValidationError
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from budget_tracker.categories.models import Category
from budget_tracker.core.exceptions import InvalidFileError
from budget_tracker.core.types import to_cents
from budget_tracker.transactions.models import Transaction
from budget_tracker.transactions.schemas import CsvRow, ImportResult, RowError

COLUMNS = ["type", "amount", "date", "description", "category"]
MAX_ROWS = 1_000_000
BATCH_SIZE = 5_000


def import_transactions(db: Session, file: BinaryIO) -> ImportResult:
    text = io.TextIOWrapper(file, encoding="utf-8-sig", newline="")
    try:
        return _import_rows(db, csv.reader(text))
    except UnicodeDecodeError as exc:
        raise InvalidFileError("The file must be a UTF-8 encoded CSV.") from exc
    except csv.Error as exc:
        raise InvalidFileError(f"The file is not a valid CSV: {exc}") from exc


def _import_rows(db: Session, reader: Iterator[list[str]]) -> ImportResult:
    header = next(reader, None)
    if header is None or [column.strip().lower() for column in header] != COLUMNS:
        raise InvalidFileError(f"The first row must be the header: {','.join(COLUMNS)}")

    category_ids = {
        category.name_normalized: category.id for category in db.scalars(select(Category))
    }

    imported = 0
    errors: list[RowError] = []
    batch: list[dict] = []

    for row_number, values in enumerate(reader, start=2):
        if row_number - 1 > MAX_ROWS:
            raise InvalidFileError(f"The file has more than {MAX_ROWS:,} rows.")
        if not values:
            continue  # Skip empty lines

        transaction, row_errors = _parse_row(values, category_ids)

        if row_errors:
            errors.append(RowError(row=row_number, errors=row_errors))
            continue

        batch.append(transaction)
        imported += 1

        if len(batch) == BATCH_SIZE:
            db.execute(insert(Transaction), batch)
            batch.clear()

    if batch:
        db.execute(insert(Transaction), batch)
    db.commit()

    return ImportResult(imported=imported, failed=len(errors), errors=errors)


def _parse_row(values: list[str], category_ids: dict[str, int]) -> tuple[dict | None, list[str]]:
    if len(values) != len(COLUMNS):
        return None, [f"Expected {len(COLUMNS)} columns, got {len(values)}."]

    try:
        row = CsvRow(**dict(zip(COLUMNS, values, strict=True)))
    except ValidationError as exc:
        return None, [f"{error['loc'][0]}: {error['msg']}" for error in exc.errors()]

    category_id = category_ids.get(row.category.casefold())
    if category_id is None:
        return None, [f"category: '{row.category}' does not exist."]

    # A bulk insert skips the model's @validates, so description_normalized is set here.

    transaction = {
        "type": row.type,
        "amount_cents": to_cents(row.amount),
        "date": row.date,
        "description": row.description,
        "description_normalized": row.description.casefold() if row.description else None,
        "category_id": category_id,
    }

    return transaction, []
