import pytest
from fastapi.testclient import TestClient


def test_create_category_trims_name_and_uppercases_color(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "  Food  ", "color": "#aabbcc"})

    assert response.status_code == 201
    assert response.json()["name"] == "Food"
    assert response.json()["color"] == "#AABBCC"


def test_create_category_rejects_duplicate_name_ignoring_case(
    client: TestClient, create_category
) -> None:
    create_category(name="Food")
    create_category(name="Šoping")

    food_again = client.post("/categories", json={"name": "FOOD", "color": "#000000"})
    shopping_again = client.post("/categories", json={"name": "šoping", "color": "#000000"})

    assert food_again.status_code == 409
    assert shopping_again.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   ", "color": "#000000"},  # blank name
        {"name": "x" * 31, "color": "#000000"},  # name too long
        {"name": "Food", "color": "#FFF"},  # color not in #RRGGBB form
        {"name": "Food"},  # color missing
    ],
)
def test_create_category_rejects_invalid_input(client: TestClient, payload: dict) -> None:
    response = client.post("/categories", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_list_categories_is_sorted_by_name(client: TestClient, create_category) -> None:
    for name in ["rent", "Car", "bills"]:
        create_category(name=name)

    response = client.get("/categories")

    assert [category["name"] for category in response.json()] == ["bills", "Car", "rent"]


def test_get_unknown_category_returns_404(client: TestClient) -> None:
    response = client.get("/categories/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_update_category_changes_only_sent_fields(client: TestClient, create_category) -> None:
    category = create_category(name="Food", color="#00AA00")

    response = client.patch(f"/categories/{category['id']}", json={"color": "#FF0000"})

    assert response.status_code == 200
    assert response.json()["name"] == "Food"
    assert response.json()["color"] == "#FF0000"


def test_update_category_allows_changing_case_of_own_name(
    client: TestClient, create_category
) -> None:
    category = create_category(name="food")

    response = client.patch(f"/categories/{category['id']}", json={"name": "Food"})

    assert response.status_code == 200
    assert response.json()["name"] == "Food"


def test_update_category_rejects_name_of_another_category(
    client: TestClient, create_category
) -> None:
    create_category(name="Food")
    rent = create_category(name="Rent")

    response = client.patch(f"/categories/{rent['id']}", json={"name": "FOOD"})

    assert response.status_code == 409


def test_delete_category(client: TestClient, create_category) -> None:
    category = create_category()

    response = client.delete(f"/categories/{category['id']}")

    assert response.status_code == 204
    assert client.get(f"/categories/{category['id']}").status_code == 404
