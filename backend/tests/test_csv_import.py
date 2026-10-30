import pytest
from fastapi.testclient import TestClient

from budget_tracker.transactions import csv_import

HEADER = "type,amount,date,description,category\n"


def upload(client: TestClient, content: str | bytes):
    return client.post("/transactions/import", files={"file": ("data.csv", content, "text/csv")})


def test_import_valid_rows(client: TestClient, create_category) -> None:
    create_category(name="Food")
    content = (
        "﻿"  # Excel adds this invisible character (BOM) at the start of UTF-8 files
        + HEADER
        + "expense,12.50,2026-10-01,Lunch,Food\n"
        + "income,100,2026-10-02,,FOOD\n"  # empty description, category in another case
    )

    response = upload(client, content)

    assert response.status_code == 200
    assert response.json() == {"imported": 2, "failed": 0, "errors": []}
    items = client.get("/transactions").json()["items"]
    assert [(t["amount"], t["description"]) for t in items] == [
        ("100.00", None),
        ("12.50", "Lunch"),
    ]


def test_import_reports_invalid_rows_and_imports_the_rest(
    client: TestClient, create_category
) -> None:
    create_category(name="Food")
    content = (
        HEADER
        + "expense,-5,2026-10-01,Bad amount,Food\n"  # row 2
        + "expense,10,2026-10-01,Good,Food\n"  # row 3
        + "expense,10,2026-10-01,No such category,Holidays\n"  # row 4
        + "expense,10,2026-10-01\n"  # row 5
    )

    response = upload(client, content)

    assert response.json() == {
        "imported": 1,
        "failed": 3,
        "errors": [
            {"row": 2, "errors": ["amount: Input should be greater than 0"]},
            {"row": 4, "errors": ["category: 'Holidays' does not exist."]},
            {"row": 5, "errors": ["Expected 5 columns, got 3."]},
        ],
    }
    assert client.get("/transactions").json()["total"] == 1


@pytest.mark.parametrize(
    "content",
    [
        "",  # empty file
        "amount,type,date\n10,expense,2026-10-01\n",  # wrong header
        (HEADER + "expense,10,2026-10-01,Šoping,Food\n").encode("cp1250"),  # not UTF-8
    ],
)
def test_import_rejects_unreadable_file(client: TestClient, content: str | bytes) -> None:
    response = upload(client, content)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_file"


def test_import_writes_full_and_partial_batches(
    client: TestClient, create_category, monkeypatch
) -> None:
    monkeypatch.setattr(csv_import, "BATCH_SIZE", 2)
    create_category(name="Food")
    rows = "".join(f"expense,{day},2026-10-0{day},,Food\n" for day in range(1, 6))

    response = upload(client, HEADER + rows)

    assert response.json()["imported"] == 5
    assert client.get("/transactions").json()["total"] == 5


def test_import_rejects_too_many_rows_and_imports_nothing(
    client: TestClient, create_category, monkeypatch
) -> None:
    monkeypatch.setattr(csv_import, "MAX_ROWS", 2)
    monkeypatch.setattr(csv_import, "BATCH_SIZE", 1)  # so rows are written before the error
    create_category(name="Food")

    response = upload(client, HEADER + "expense,10,2026-10-01,,Food\n" * 3)

    assert response.status_code == 400
    assert client.get("/transactions").json()["total"] == 0
