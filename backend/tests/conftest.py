from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from budget_tracker.core.database import Base, create_db_engine, get_db
from budget_tracker.main import API_PREFIX, app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """API client that uses a fresh, empty test database for every test."""
    engine = create_db_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, base_url=f"http://testserver{API_PREFIX}")
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def create_category(client: TestClient) -> Callable[..., dict[str, Any]]:
    """Helper that creates a category through the API and returns it."""

    def _create(name: str = "Food", color: str = "#00AA00") -> dict[str, Any]:
        response = client.post("/categories", json={"name": name, "color": color})
        assert response.status_code == 201, response.text
        return response.json()

    return _create
