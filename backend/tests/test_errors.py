from fastapi.testclient import TestClient


def test_malformed_json_returns_explained_error_instead_of_crashing(client: TestClient) -> None:
    response = client.post(
        "/categories", content="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
