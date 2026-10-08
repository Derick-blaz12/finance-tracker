# Finance Tracker

A command-line personal finance tracker in Python, built step by step
while learning software engineering fundamentals.

## Features
- Add, view, edit and delete income and expenses
- Categories and dates, with input validation
- Search by keyword, type, exact date, month or date range
- Statistics: totals, largest and average expense, spending by category, monthly summary
- SQLite storage with permanent transaction ids
- 265 automated tests
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
| `money.py` | naira text to integer kobo and back |
| `app.py` |  |
| `users.py` |  |
| `ratelimit.py` |  |
| `templates/` |  |
| `static/` |  |

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

## History
Early versions stored data in a JSON file. That code was removed after the
move to SQLite; it remains in the Git history (see the `v2.0` tag).

## Run the web app
    $env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
    python -m flask --app app:create_app run --debug

## Security
- Passwords hashed (werkzeug), emails unique and case-insensitive
- Every query scoped to the logged-in user, tested with two accounts
- CSRF tokens on every POST form
- Failed-login rate limiting by email and IP
- `SECRET_KEY` and `PRODUCTION=1` come from environment variables, never the repo

## Before deploying
- Run with gunicorn behind HTTPS, set `PRODUCTION=1`
- Configure trusted proxy headers so rate limiting sees real client IPs
- Put the SQLite file on persistent disk and back it up