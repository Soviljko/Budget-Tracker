from pydantic import BaseModel, ConfigDict

from budget_tracker.core.types import CategoryName, HexColor


class CategoryCreate(BaseModel):
    name: CategoryName
    color: HexColor


class CategoryUpdate(BaseModel):
    name: CategoryName | None = None
    color: HexColor | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
