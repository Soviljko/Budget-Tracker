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


def test_category_with_transactions_cannot_be_deleted(
    client: TestClient, create_category, create_transaction
) -> None:
    food = create_category(name="Food")
    create_transaction(category_id=food["id"])

    response = client.delete(f"/categories/{food['id']}")

    assert response.status_code == 409
    assert client.get(f"/categories/{food['id']}").status_code == 200
