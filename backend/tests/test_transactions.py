import pytest
from fastapi.testclient import TestClient


def test_create_transaction(client: TestClient, create_category) -> None:
    food = create_category(name="Food")
    payload = {
        "type": "expense",
        "amount": "12.5",
        "date": "2026-10-08",
        "description": "  Lunch ",
        "category_id": food["id"],
    }

    response = client.post("/transactions", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "12.50"
    assert body["description"] == "Lunch"
    assert body["type"] == "expense"
    assert body["date"] == "2026-10-08"


def test_empty_description_means_no_description(client: TestClient, create_category) -> None:
    food = create_category(name="Food")
    payload = {
        "type": "income",
        "amount": "300",
        "date": "2026-10-09",
        "description": "",
        "category_id": food["id"],
    }

    response = client.post("/transactions", json=payload)

    assert response.status_code == 201
    assert response.json()["description"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("type", "transfer"),  # only income or expense
        ("amount", "0"),  # must be greater than 0
        ("amount", "12.345"),  # at most 2 decimals
        ("amount", "1000000.01"),  # at most 1,000,000.00
        ("date", "2026-02-30"),  # not a real date
        ("description", "x" * 201),  # at most 200 characters
        ("category_id", None),  # required
    ],
)
def test_create_transaction_rejects_invalid_input(
    client: TestClient, create_category, field: str, value: object
) -> None:
    food = create_category(name="Food")
    payload = {"type": "expense", "amount": "10", "date": "2026-10-08", "category_id": food["id"]}
    payload[field] = value

    response = client.post("/transactions", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == f"body.{field}"


def test_create_transaction_rejects_unknown_category(client: TestClient) -> None:
    payload = {"type": "expense", "amount": "10", "date": "2026-10-08", "category_id": 999}

    response = client.post("/transactions", json=payload)

    assert response.status_code == 404


def test_get_transaction(client: TestClient, create_transaction) -> None:
    transaction = create_transaction(amount="5.00")

    response = client.get(f"/transactions/{transaction['id']}")

    assert response.status_code == 200
    assert response.json() == transaction


def test_update_transaction_replaces_all_fields(
    client: TestClient, create_category, create_transaction
) -> None:
    transaction = create_transaction(type="expense", amount="5.00", description="Old")
    salary = create_category(name="Salary")
    payload = {
        "type": "income",
        "amount": "2000",
        "date": "2026-11-01",
        "description": "New",
        "category_id": salary["id"],
    }

    response = client.put(f"/transactions/{transaction['id']}", json=payload)

    assert response.status_code == 200
    assert response.json() == {**payload, "id": transaction["id"], "amount": "2000.00"}


def test_delete_transaction(client: TestClient, create_transaction) -> None:
    transaction = create_transaction()

    response = client.delete(f"/transactions/{transaction['id']}")

    assert response.status_code == 204
    assert client.get(f"/transactions/{transaction['id']}").status_code == 404
