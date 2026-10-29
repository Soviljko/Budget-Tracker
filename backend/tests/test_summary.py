from fastapi.testclient import TestClient


def test_empty_month_shows_zeros_and_no_categories(client: TestClient) -> None:
    response = client.get("/summary/2026-10")

    assert response.status_code == 200
    assert response.json() == {
        "month": "2026-10",
        "total_income": "0.00",
        "total_expense": "0.00",
        "balance": "0.00",
        "categories": [],
    }


def test_summary_totals_and_categories(
    client: TestClient, create_category, create_transaction
) -> None:
    salary = create_category(name="Salary")
    food = create_category(name="Food")
    rent = create_category(name="Rent")
    fun = create_category(name="Fun")
    create_transaction(category_id=salary["id"], type="income", amount="2000.00")
    create_transaction(category_id=food["id"], amount="250.00")
    create_transaction(category_id=food["id"], amount="100.50")
    create_transaction(category_id=rent["id"], amount="600.00")
    client.put(f"/budgets/2026-10/{food['id']}", json={"amount": "300"})
    client.put(f"/budgets/2026-10/{fun['id']}", json={"amount": "80"})

    summary = client.get("/summary/2026-10").json()

    assert summary["total_income"] == "2000.00"
    assert summary["total_expense"] == "950.50"
    assert summary["balance"] == "1049.50"
    rows = [(c["name"], c["spent"], c["budget"], c["left"]) for c in summary["categories"]]
    assert rows == [
        ("Rent", "600.00", None, None),  # expense without a budget
        ("Food", "350.50", "300.00", "-50.50"),  # over budget
        ("Fun", "0.00", "80.00", "80.00"),  # budget without an expense
    ]


def test_categories_with_same_expense_are_sorted_by_name(
    client: TestClient, create_category, create_transaction
) -> None:
    for name in ["Rent", "bills", "Car"]:
        category = create_category(name=name)
        create_transaction(category_id=category["id"], amount="50.00")

    summary = client.get("/summary/2026-10").json()

    assert [category["name"] for category in summary["categories"]] == ["bills", "Car", "Rent"]


def test_summary_counts_only_transactions_from_that_month(
    client: TestClient, create_transaction
) -> None:
    create_transaction(date="2026-09-30", amount="1.00")
    create_transaction(date="2026-10-01", amount="10.00")
    create_transaction(date="2026-10-31", amount="20.00")
    create_transaction(date="2026-11-01", amount="300.00")

    summary = client.get("/summary/2026-10").json()

    assert summary["total_expense"] == "30.00"
