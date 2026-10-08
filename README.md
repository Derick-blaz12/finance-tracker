# Finance Tracker

A command-line personal finance tracker in Python, built step by step
while learning software engineering fundamentals.

## Features
- Add, view, edit and delete income and expenses
- Categories and dates, with input validation
- Search by keyword, type, exact date, month or date range
- Statistics: totals, largest and average expense, spending by category, monthly summary
- SQLite storage with permanent transaction ids
- 151 automated tests
- Money stored as integer kobo, so totals are exact (no floating-point errors)

## Architecture
| File | Job |
|---|---|
| `main.py` | menu loop |
| `tracker.py` | user flows and display |
| `calculations.py` | pure math, no printing or input |
| `filters.py` | pure date filtering |
| `input_helpers.py` | asking the user for validated input |
| `database.py` | SQLite add, read, update, delete by id |
| `models.py` | `Transaction` dataclass that validates itself |
| `migrate.py`, `storage.py` | one-time import from the earlier JSON version |
| `money.py` | naira text to integer kobo and back |

## Run it
    python main.py

| `tests/` | automated tests (pytest) |

## Run the tests
    pip install -r requirements.txt
    python -m pytest -q

Your data lives in `finance.db`, which is created on first run and is not
part of the repository.

## What I learned
- Separating input, logic, display and storage
- Refactoring in small steps with tests as a safety net
- Replacing loose dictionaries with a validated class
- Parameterized SQL, commits, and database ids vs list positions
- Testing with fake input and in-memory databases