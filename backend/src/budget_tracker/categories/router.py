from fastapi import APIRouter, status

from budget_tracker.categories import service
from budget_tracker.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from budget_tracker.core.database import DbSession
from budget_tracker.core.exceptions import error_responses
from budget_tracker.core.types import Id

router = APIRouter(
    prefix="/categories", tags=["categories"], responses=error_responses(404, 409, 422)
)


@router.get("")
def list_categories(db: DbSession) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in service.list_categories(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.create_category(db, data))


@router.get("/{category_id}")
def get_category(category_id: Id, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.get_category(db, category_id))


@router.patch("/{category_id}")
def update_category(category_id: Id, data: CategoryUpdate, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(service.update_category(db, category_id, data))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: Id, db: DbSession) -> None:
    service.delete_category(db, category_id)
