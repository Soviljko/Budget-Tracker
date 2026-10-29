from fastapi import APIRouter, status

from budget_tracker.core.database import DbSession
from budget_tracker.transactions import service
from budget_tracker.transactions.schemas import TransactionInput, TransactionRead

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionInput, db: DbSession) -> TransactionRead:
    return TransactionRead.from_model(service.create_transaction(db, data))


@router.get("/{transaction_id}")
def get_transaction(transaction_id: int, db: DbSession) -> TransactionRead:
    return TransactionRead.from_model(service.get_transaction(db, transaction_id))


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int, data: TransactionInput, db: DbSession
) -> TransactionRead:
    return TransactionRead.from_model(service.update_transaction(db, transaction_id, data))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: DbSession) -> None:
    service.delete_transaction(db, transaction_id)
