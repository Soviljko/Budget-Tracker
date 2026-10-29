from fastapi import APIRouter, status

from budget_tracker.categories import service
from budget_tracker.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from budget_tracker.core.database import DbSession

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def list_categories(db: DbSession) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in service.list_categories(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.create_category(db, data))


@router.get("/{category_id}")
def get_category(category_id: int, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.get_category(db, category_id))


@router.patch("/{category_id}")
def update_category(category_id: int, data: CategoryUpdate, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.update_category(db, category_id, data))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession) -> None:
    service.delete_category(db, category_id)
