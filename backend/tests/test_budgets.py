import pytest
from fastapi.testclient import TestClient


def test_setting_budget_again_changes_it(client: TestClient, create_category) -> None:
    food = create_category(name="Food")
    client.put(f"/budgets/2026-10/{food['id']}", json={"amount": "500"})

    response = client.put(f"/budgets/2026-10/{food['id']}", json={"amount": "650.50"})

    assert response.status_code == 200
    budgets = client.get("/budgets", params={"month": "2026-10"}).json()
    assert len(budgets) == 1
    assert budgets[0]["amount"] == "650.50"


def test_list_budgets_shows_only_that_month(client: TestClient, create_category) -> None:
    food = create_category(name="Food")
    client.put(f"/budgets/2026-10/{food['id']}", json={"amount": "100"})
    client.put(f"/budgets/2026-11/{food['id']}", json={"amount": "200"})

    response = client.get("/budgets", params={"month": "2026-11"})

    assert [budget["amount"] for budget in response.json()] == ["200.00"]


@pytest.mark.parametrize(
    ("month", "amount"),
    [
        ("2026-13", "100"),  # not a real month
        ("2026-1", "100"),  # wrong format
        ("2026-10", "0"),  # amount must be greater than 0
    ],
)
def test_set_budget_rejects_invalid_input(
    client: TestClient, create_category, month: str, amount: str
) -> None:
    food = create_category(name="Food")

    response = client.put(f"/budgets/{month}/{food['id']}", json={"amount": amount})

    assert response.status_code == 422


def test_delete_budget(client: TestClient, create_category) -> None:
    food = create_category(name="Food")
    client.put(f"/budgets/2026-10/{food['id']}", json={"amount": "100"})

    response = client.delete(f"/budgets/2026-10/{food['id']}")

    assert response.status_code == 204
    assert client.get("/budgets", params={"month": "2026-10"}).json() == []


def test_deleting_category_also_deletes_its_budgets(client: TestClient, create_category) -> None:
    food = create_category(name="Food")
    client.put(f"/budgets/2026-10/{food['id']}", json={"amount": "100"})

    client.delete(f"/categories/{food['id']}")

    assert client.get("/budgets", params={"month": "2026-10"}).json() == []
