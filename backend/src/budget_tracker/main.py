from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from budget_tracker.budgets.models import Budget  # noqa: F401
from budget_tracker.categories.models import Category  # noqa: F401
from budget_tracker.categories.router import router as categories_router
from budget_tracker.core.database import Base, engine
from budget_tracker.core.exceptions import register_exception_handlers
from budget_tracker.transactions.models import Transaction  # noqa: F401
from budget_tracker.transactions.router import router as transactions_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Budget Tracker API", version="1.0.0", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(categories_router, prefix=API_PREFIX)
app.include_router(transactions_router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
