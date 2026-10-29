from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from budget_tracker.categories.models import Category
from budget_tracker.categories.schemas import CategoryCreate, CategoryUpdate
from budget_tracker.core.exceptions import ConflictError, NotFoundError
from budget_tracker.transactions.models import Transaction


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name_normalized)))


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError(f"Category {category_id} not found.")

    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    _ensure_name_is_free(db, data.name)
    category = Category(name=data.name, color=data.color)
    db.add(category)
    db.commit()
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    if data.name is not None:
        _ensure_name_is_free(db, data.name, exclude_id=category_id)
        category.name = data.name
    if data.color is not None:
        category.color = data.color
    db.commit()
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    has_transactions = db.scalar(select(exists().where(Transaction.category_id == category_id)))
    if has_transactions:
        raise ConflictError(f"Category {category_id} has transactions and cannot be deleted.")
    db.delete(category)
    db.commit()


def _ensure_name_is_free(db: Session, name: str, exclude_id: int | None = None) -> None:
    query = select(Category.id).where(Category.name_normalized == name.casefold())
    if exclude_id is not None:
        query = query.where(Category.id != exclude_id)
    if db.scalar(query) is not None:
        raise ConflictError(f"Category '{name}' already exists.")
