from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from budget_tracker.core.database import Base, engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Budget Tracker API", version="1.0.0", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
