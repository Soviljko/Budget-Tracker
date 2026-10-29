from fastapi.testclient import TestClient


def test_unknown_route_uses_our_error_format(client: TestClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "http_error", "message": "Not Found", "details": []}
    }


def test_malformed_json_returns_422_instead_of_crashing(client: TestClient) -> None:
    response = client.post(
        "/categories", content="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
