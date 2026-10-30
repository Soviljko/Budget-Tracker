from typing import Annotated

from fastapi import APIRouter, Query, UploadFile, status

from budget_tracker.core.database import DbSession
from budget_tracker.core.exceptions import error_responses
from budget_tracker.core.types import Id
from budget_tracker.transactions import csv_import, service
from budget_tracker.transactions.schemas import (
    ImportResult,
    TransactionInput,
    TransactionPage,
    TransactionQuery,
    TransactionRead,
)

router = APIRouter(
    prefix="/transactions", tags=["transactions"], responses=error_responses(404, 422)
)


@router.get("")
def list_transactions(
    params: Annotated[TransactionQuery, Query()], db: DbSession
) -> TransactionPage:
    items, total = service.list_transactions(db, params)
    return TransactionPage(
        items=[TransactionRead.from_model(t) for t in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionInput, db: DbSession) -> TransactionRead:
    return TransactionRead.from_model(service.create_transaction(db, data))


@router.post("/import", responses=error_responses(400))
def import_transactions(file: UploadFile, db: DbSession) -> ImportResult:
    return csv_import.import_transactions(db, file.file)


@router.get("/{transaction_id}")
def get_transaction(transaction_id: Id, db: DbSession) -> TransactionRead:
    return TransactionRead.from_model(service.get_transaction(db, transaction_id))


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: Id, data: TransactionInput, db: DbSession
) -> TransactionRead:
    return TransactionRead.from_model(service.update_transaction(db, transaction_id, data))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: Id, db: DbSession) -> None:
    service.delete_transaction(db, transaction_id)
