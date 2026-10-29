from fastapi.testclient import TestClient


def descriptions(response) -> list[str]:
    return [item["description"] for item in response.json()["items"]]


def test_list_is_newest_first_and_last_added_first_on_same_date(
    client: TestClient, create_transaction
) -> None:
    create_transaction(date="2026-10-01", description="old")
    create_transaction(date="2026-10-05", description="same day, added first")
    create_transaction(date="2026-10-05", description="same day, added last")
    create_transaction(date="2026-10-03", description="middle")

    response = client.get("/transactions")

    assert response.status_code == 200
    assert descriptions(response) == [
        "same day, added last",
        "same day, added first",
        "middle",
        "old",
    ]


def test_list_is_paginated(client: TestClient, create_transaction) -> None:
    for day in range(1, 6):
        create_transaction(date=f"2026-10-0{day}", description=f"day {day}")

    first_page = client.get("/transactions", params={"page": 1, "page_size": 2}).json()
    last_page = client.get("/transactions", params={"page": 3, "page_size": 2}).json()

    assert first_page["total"] == 5
    assert [t["description"] for t in first_page["items"]] == ["day 5", "day 4"]
    assert [t["description"] for t in last_page["items"]] == ["day 1"]


def test_filter_by_date_range_includes_both_dates(client: TestClient, create_transaction) -> None:
    for day in ["2026-09-30", "2026-10-01", "2026-10-15", "2026-10-31", "2026-11-01"]:
        create_transaction(date=day, description=day)

    response = client.get(
        "/transactions", params={"date_from": "2026-10-01", "date_to": "2026-10-31"}
    )

    assert descriptions(response) == ["2026-10-31", "2026-10-15", "2026-10-01"]


def test_filter_by_category_type_and_text_combined(
    client: TestClient, create_category, create_transaction
) -> None:
    food = create_category(name="Food")
    other = create_category(name="Other")
    create_transaction(category_id=food["id"], type="expense", description="Lunch at work")
    create_transaction(category_id=food["id"], type="expense", description="Dinner")
    create_transaction(category_id=food["id"], type="income", description="Lunch refund")
    create_transaction(category_id=other["id"], type="expense", description="Lunch box")

    response = client.get(
        "/transactions",
        params={"category_id": food["id"], "type": "expense", "search": "LUNCH"},
    )

    assert descriptions(response) == ["Lunch at work"]
