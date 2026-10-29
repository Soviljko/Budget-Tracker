from sqlalchemy import func, select
from sqlalchemy.orm import Session

from budget_tracker.categories.service import get_category
from budget_tracker.core.exceptions import NotFoundError
from budget_tracker.core.types import to_cents
from budget_tracker.transactions.models import Transaction
from budget_tracker.transactions.schemas import TransactionInput, TransactionQuery


def list_transactions(db: Session, params: TransactionQuery) -> tuple[list[Transaction], int]:
    query = select(Transaction)
    if params.date_from is not None:
        query = query.where(Transaction.date >= params.date_from)
    if params.date_to is not None:
        query = query.where(Transaction.date <= params.date_to)
    if params.category_id is not None:
        query = query.where(Transaction.category_id == params.category_id)
    if params.type is not None:
        query = query.where(Transaction.type == params.type)
    if params.search:
        query = query.where(
            Transaction.description_normalized.contains(params.search.casefold(), autoescape=True)
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(params.page_size)
        .offset((params.page - 1) * params.page_size)
    )

    return list(items), total


def get_transaction(db: Session, transaction_id: int) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise NotFoundError(f"Transaction {transaction_id} not found.")
    return transaction


def create_transaction(db: Session, data: TransactionInput) -> Transaction:
    transaction = Transaction()
    _apply_input(db, transaction, data)
    db.add(transaction)
    db.commit()
    return transaction


def update_transaction(db: Session, transaction_id: int, data: TransactionInput) -> Transaction:
    transaction = get_transaction(db, transaction_id)
    _apply_input(db, transaction, data)
    db.commit()
    return transaction


def delete_transaction(db: Session, transaction_id: int) -> None:
    transaction = get_transaction(db, transaction_id)
    db.delete(transaction)
    db.commit()


def _apply_input(db: Session, transaction: Transaction, data: TransactionInput) -> None:
    get_category(db, data.category_id)
    transaction.type = data.type
    transaction.amount_cents = to_cents(data.amount)
    transaction.date = data.date
    transaction.description = data.description
    transaction.category_id = data.category_id
