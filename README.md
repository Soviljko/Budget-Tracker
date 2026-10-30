# Budget Tracker API

REST API for a personal budget tracker: record income and expenses, sort them into
categories, set a monthly budget per category, import transactions from CSV and see a
summary for each month.

Built with Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2 and SQLite.

## Getting started

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). It installs the
right Python version and all dependencies by itself. Run every command from the `backend`
folder:

```bash
cd backend
```

### Run the app

```bash
uv sync
uv run fastapi dev src/budget_tracker/main.py
```

The API runs at <http://127.0.0.1:8000>. Interactive documentation is at
<http://127.0.0.1:8000/docs>.

Data is stored in `budget.db` in the `backend` folder and stays there after a restart. To
use another location, copy `.env.example` to `.env` and change `DATABASE_URL`.

### Run the tests

```bash
uv run pytest
```

Tests use a temporary database, so they never touch `budget.db`. To check code style, run
`uv run ruff check .`

### Data command

Fill the database with sample data: 8 categories, 3 months of transactions and budgets.

```bash
uv run python -m budget_tracker.seed
```

The command refuses to add data to a database that already has some. To delete everything
and start over, run:

```bash
uv run python -m budget_tracker.seed --reset
```

Generate a large CSV file to try the import. Run the first command above before importing,
because the file uses the sample categories. About 1 row in 5,000 is invalid on purpose, so
you can see the error report.

```bash
uv run python -m budget_tracker.seed --csv data/transactions.csv --rows 1000000
curl -F "file=@data/transactions.csv" http://127.0.0.1:8000/api/v1/transactions/import
```

In Windows PowerShell, write `curl.exe` instead of `curl`.

## API

All endpoints except `/health` start with `/api/v1`. The full schema of every input and
output is in `/docs` and `/openapi.json`.

| Method | Path | Input | Output |
|---|---|---|---|
| GET | `/health` | | `{"status": "ok"}` |
| GET | `/categories` | | Categories sorted by name |
| POST | `/categories` | `name`, `color` | 201, the category |
| GET | `/categories/{id}` | | The category |
| PATCH | `/categories/{id}` | `name` and/or `color` | The category |
| DELETE | `/categories/{id}` | | 204, also deletes its budgets; 409 if it has transactions |
| GET | `/transactions` | Query, see below | Page of transactions |
| POST | `/transactions` | `type`, `amount`, `date`, `category_id`, optional `description` | 201, the transaction |
| GET | `/transactions/{id}` | | The transaction |
| PUT | `/transactions/{id}` | Same as POST | The transaction |
| DELETE | `/transactions/{id}` | | 204 |
| POST | `/transactions/import` | Multipart form field `file` | Import report |
| GET | `/budgets?month=2026-10` | | Budgets of the month |
| PUT | `/budgets/{month}/{category_id}` | `amount` | The budget (creates or changes it) |
| DELETE | `/budgets/{month}/{category_id}` | | 204 |
| GET | `/summary/{month}` | | Monthly summary |

A month is written as `YYYY-MM` and a date as `YYYY-MM-DD`. Amounts can be sent as a number
or a string, and are always returned as a string with 2 decimals, such as `"12.50"`.

A category, a transaction and a budget look like this:

```json
{ "id": 1, "name": "Food", "color": "#00AA00" }
```

```json
{
  "id": 7,
  "type": "expense",
  "amount": "12.50",
  "date": "2026-10-08",
  "description": "Lunch",
  "category_id": 1
}
```

```json
{ "id": 3, "category_id": 1, "month": "2026-10", "amount": "300.00" }
```

### Listing transactions

`GET /transactions` returns the newest first. On the same date, the one added last comes
first. All filters are optional and can be combined.

| Query | Meaning |
|---|---|
| `date_from`, `date_to` | Date range, both dates included |
| `category_id` | Only this category |
| `type` | `income` or `expense` |
| `search` | Text in the description, ignoring upper and lower case |
| `page`, `page_size` | Page number (default 1) and rows per page (default 20, at most 100) |

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```

### Importing a CSV file

The file must be UTF-8 with commas as separators, and its first row must be the header:

```csv
type,amount,date,description,category
expense,12.50,2026-10-08,Lunch,Eating out
income,300.00,2026-10-09,,Other
```

Valid rows are imported even when others fail. `row` counts rows the way a spreadsheet
does, and the header is row 1.

```json
{
  "imported": 1,
  "failed": 1,
  "errors": [{ "row": 3, "errors": ["amount: Input should be greater than 0"] }]
}
```

A file that cannot be read as a whole (empty, wrong header, not UTF-8, or more than
1,000,000 rows) returns 400 and nothing is imported.

### Monthly summary

`budget` and `left` are `null` for a category that has no budget in that month. `left` is
negative when the category is over budget. Categories are sorted by highest expense, then
by name. A month with no transactions and no budgets shows zeros and no categories.

```json
{
  "month": "2026-10",
  "total_income": "2000.00",
  "total_expense": "350.50",
  "balance": "1649.50",
  "categories": [
    { "category_id": 2, "name": "Food", "spent": "350.50", "budget": "300.00", "left": "-50.50" },
    { "category_id": 4, "name": "Fun", "spent": "0.00", "budget": "80.00", "left": "80.00" }
  ]
}
```

### Errors

Every error has the same form. `details` lists the invalid fields and is empty for other
errors.

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input.",
    "details": [{ "field": "body.name", "message": "String should have at least 1 character" }]
  }
}
```

| Status | Code | When |
|---|---|---|
| 400 | `invalid_file` | The uploaded file cannot be read |
| 404 | `not_found` | The resource does not exist |
| 409 | `conflict` | A broken rule, such as a duplicate category name |
| 422 | `validation_error` | Invalid input |
| 500 | `internal_error` | An unexpected error |

Errors from the framework, such as an unknown route, use the code `http_error`.

## Project structure

Code is grouped by feature. Each feature has three layers, and each layer only talks to the
one below it:

```text
router (HTTP)  ->  service (business rules)  ->  SQLAlchemy session (database)
```

```text
backend/src/budget_tracker/
├── main.py           creates the app
├── seed.py           data command
├── core/             settings, database, error handling, shared validation types
├── categories/       models, schemas, service, router
├── transactions/     the same, plus csv_import.py
├── budgets/          models, schemas, service, router
└── summary/          schemas, service, router (no table, it is calculated)
```

## Design decisions

- **Money is stored in cents.** `12.50` is saved as the whole number `1250`. Decimal numbers
  in a float can have rounding errors, and whole numbers do not.
- **Validation rules are in one place.** `core/types.py` has the rules for amounts, names
  and months. The API and the CSV import use the same rules, so they cannot be different.
- **Text is compared in Python, not in SQLite.** SQLite's `lower()` works only for English
  letters, so it does not see `č` and `Č` as the same letter. That is why names and
  descriptions are saved a second time with `casefold()`, in a separate column. Unique names
  and search use that column.
- **There is no repository layer.** Services use the SQLAlchemy session directly. The session
  already hides the database, so one more layer would only pass the calls along.
- **The database also checks the rules.** Unique constraints and foreign keys protect the
  data if a check in the code is missed. SQLite does not check foreign keys by default, so
  `PRAGMA foreign_keys = ON` is set on every connection.
- **The database calculates the summary.** `SUM` and `GROUP BY` return only the final
  numbers, so the app does not load all transactions of the month into memory.
- **The CSV import handles large files.**
  - The file is read row by row, so it is never all in memory.
  - Categories are loaded once into a dictionary, so there is no query for every row.
  - Rows are saved in batches of 5,000, which is much faster than one ORM object per row.
    One million rows took about 25 seconds, and about 70 seconds with ORM objects.
  - There is one commit at the end, so an import that stops halfway saves nothing.

## Limitations and next steps

I left these out to keep the project simple:

- **No migrations.** Tables are created when the app starts, with `create_all`. A real
  project would use Alembic, so the tables can change without losing data.
- **SQLite instead of PostgreSQL.** SQLite is enough for one user. To move to PostgreSQL,
  change `DATABASE_URL`, add the PostgreSQL driver and run the tests.
- **The import runs during the request.** The user has to wait until it ends. For very large
  files, a background job would be better.
- **The import report has no size limit.** All failed rows are listed, so a large file with
  many errors gives a large response.
- **A CSV row may not show all its errors.** The category is checked last, so a row with a
  bad amount and an unknown category reports only the amount.
- **Duplicates are not detected.** Two identical transactions can both be real, so importing
  the same file twice adds its rows twice.
