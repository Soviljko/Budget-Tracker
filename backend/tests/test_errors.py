import pytest
from fastapi.testclient import TestClient


def test_malformed_json_returns_explained_error_instead_of_crashing(client: TestClient) -> None:
    response = client.post(
        "/categories", content="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize(
    "path",
    [
        "/categories/{huge}",
        "/transactions/{huge}",
        "/transactions?category_id={huge}",
        "/transactions?page={huge}",
    ],
)
def test_too_large_number_returns_explained_error(client: TestClient, path: str) -> None:
    response = client.get(path.format(huge=10**30))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
