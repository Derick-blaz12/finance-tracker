import sqlite3

import pytest

import database
import tracker
from helpers import fake_inputs
from models import Transaction


@pytest.fixture(autouse=True)
def database_connection(monkeypatch):
    """A fresh in-memory database for every test. Your real finance.db is never touched."""
    connection = sqlite3.connect(":memory:")
    database.create_table(connection)
    monkeypatch.setattr(tracker, "connection", connection)
    yield connection
    connection.close()


def add(kind, description, amount, category=None, date="2026-10-04"):
    """Test helper: put a transaction straight into the database."""
    database.add_transaction(
        tracker.connection, Transaction(kind, description, amount, date, category)
    )


# ---------- printing ----------

def test_largest_expense_picks_biggest_and_ignores_income(capsys):
    add("income", "Salary", 200000)
    add("expense", "Rice", 5000, "Food")
    add("expense", "Rent", 120000, "Bills")
    tracker.largest_expense()
    out = capsys.readouterr().out
    assert "Rent" in out
    assert "3." in out
    assert "Rice" not in out
    assert "Salary" not in out


def test_largest_expense_with_no_expenses(capsys):
    add("income", "Salary", 50000)
    tracker.largest_expense()
    assert "No expenses yet." in capsys.readouterr().out


def test_average_expense_with_no_expenses(capsys):
    add("income", "Salary", 50000)
    tracker.average_expense()
    assert "No expenses yet." in capsys.readouterr().out


def test_spending_by_category_with_no_expenses(capsys):
    add("income", "Salary", 50000)
    tracker.spending_by_category()
    assert "No expenses yet." in capsys.readouterr().out


# ---------- search by type ----------

def test_search_by_type_income_only(monkeypatch, capsys):
    add("income", "Salary", 50000)
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["1"])
    tracker.search_by_type()
    out = capsys.readouterr().out
    assert "Salary" in out
    assert "Rice" not in out


def test_search_by_type_expense_keeps_original_numbers(monkeypatch, capsys):
    add("income", "Salary", 50000)
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["2"])
    tracker.search_by_type()
    out = capsys.readouterr().out
    assert "2. " in out
    assert "Salary" not in out


# ---------- search menu ----------

def test_search_menu_with_no_transactions(capsys):
    tracker.search_transactions()
    assert "No transactions to search." in capsys.readouterr().out


def test_search_menu_cancel(monkeypatch, capsys):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["4"])
    tracker.search_transactions()
    assert "Cancelled." in capsys.readouterr().out


# ---------- date search ----------

def test_search_menu_routes_to_date_search(monkeypatch, capsys):
    add("income", "Salary", 50000, date="2026-10-01")
    fake_inputs(monkeypatch, ["3", "4"])   # Search by date -> Cancel
    tracker.search_transactions()
    assert "Cancelled." in capsys.readouterr().out


def test_search_by_exact_date(monkeypatch, capsys):
    add("income", "Salary", 50000, date="2026-10-01")
    add("expense", "Rice", 5000, "Food", date="2026-10-07")
    add("expense", "Bus fare", 2000, "Transport", date="2026-10-07")
    fake_inputs(monkeypatch, ["2026-10-07"])
    tracker.search_by_exact_date()
    out = capsys.readouterr().out
    assert "Rice" in out and "Bus fare" in out
    assert "Salary" not in out
    assert "2. " in out and "3. " in out   # original numbers kept


def test_search_by_exact_date_no_match(monkeypatch, capsys):
    add("income", "Salary", 50000, date="2026-10-01")
    fake_inputs(monkeypatch, ["2026-01-01"])
    tracker.search_by_exact_date()
    assert "No transactions found on 2026-01-01." in capsys.readouterr().out


def test_search_by_month(monkeypatch, capsys):
    add("income", "Salary", 50000, date="2026-10-01")
    add("expense", "Shoes", 20000, "Shopping", date="2026-09-28")
    fake_inputs(monkeypatch, ["2026-10"])
    tracker.search_by_month()
    out = capsys.readouterr().out
    assert "Salary" in out
    assert "Shoes" not in out


def test_search_by_range(monkeypatch, capsys):
    add("income", "Salary", 50000, date="2026-10-01")
    add("expense", "Rice", 5000, "Food", date="2026-10-07")
    add("expense", "Shoes", 20000, "Shopping", date="2026-09-28")
    fake_inputs(monkeypatch, ["2026-10-01", "2026-10-07"])
    tracker.search_by_range()
    out = capsys.readouterr().out
    assert "Salary" in out and "Rice" in out
    assert "Shoes" not in out


def test_search_by_range_asks_again_when_start_is_after_end(monkeypatch, capsys):
    add("expense", "Rice", 5000, "Food", date="2026-10-05")
    # first attempt is backwards, second attempt is valid
    fake_inputs(monkeypatch, ["2026-10-07", "2026-10-01", "2026-10-01", "2026-10-07"])
    tracker.search_by_range()
    out = capsys.readouterr().out
    assert "cannot be after" in out
    assert "Rice" in out

def test_search_menu_routes_to_type_search(monkeypatch, capsys):
    add("income", "Salary", 50000)
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["2", "1"])
    tracker.search_transactions()
    out = capsys.readouterr().out
    assert "Salary" in out
    assert "Rice" not in out


# ---------- statistics menu ----------

def test_statistics_total_income(monkeypatch, capsys):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["1"])
    tracker.show_statistics()
    assert "Total income: ₦50,000.00" in capsys.readouterr().out


def test_statistics_average_expense(monkeypatch, capsys):
    add("expense", "A", 10000, "Other")
    add("expense", "B", 30000, "Other")
    fake_inputs(monkeypatch, ["4"])
    tracker.show_statistics()
    assert "₦20,000.00" in capsys.readouterr().out


def test_statistics_cancel(monkeypatch, capsys):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["7"])
    tracker.show_statistics()
    assert "Cancelled." in capsys.readouterr().out


# ---------- edit menu ----------

def test_edit_with_no_transactions(capsys):
    tracker.edit_transaction()
    assert "No transactions to edit." in capsys.readouterr().out


def test_edit_expense_amount(monkeypatch):
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["1", "3", "6500"])
    tracker.edit_transaction()
    t = tracker.load_transactions()[0]
    assert t.amount == 6500
    assert t.description == "Rice"


def test_edit_expense_cancel_changes_nothing(monkeypatch, capsys):
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["1", "5"])
    tracker.edit_transaction()
    assert "Cancelled." in capsys.readouterr().out
    assert tracker.load_transactions()[0].amount == 5000


def test_edit_income_menu_has_no_category(monkeypatch, capsys):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["1", "4"])
    tracker.edit_transaction()
    out = capsys.readouterr().out
    assert "Category" not in out
    assert "Cancelled." in out


def test_edit_income_amount_does_not_add_category(monkeypatch):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["1", "2", "999"])
    tracker.edit_transaction()
    t = tracker.load_transactions()[0]
    assert t.amount == 999
    assert t.category is None


# ---------- database changes ----------

def test_add_transaction_saves_to_database(monkeypatch):
    fake_inputs(monkeypatch, ["Salary", "50000", ""])
    tracker.add_transaction("income")
    saved = tracker.load_transactions()
    assert len(saved) == 1
    assert saved[0].description == "Salary"


def test_edit_saves_to_database(monkeypatch):
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["1", "3", "6500"])
    tracker.edit_transaction()
    assert tracker.load_transactions()[0].amount == 6500


def test_delete_saves_to_database(monkeypatch):
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["1", "y"])
    tracker.delete_transaction()
    assert tracker.load_transactions() == []


def test_cancelled_delete_keeps_the_row(monkeypatch):
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["1", "n"])
    tracker.delete_transaction()
    assert len(tracker.load_transactions()) == 1


def test_edit_after_delete_changes_the_right_row(monkeypatch):
    add("expense", "A", 100, "Other")
    add("expense", "B", 200, "Other")
    add("expense", "C", 300, "Other")
    fake_inputs(monkeypatch, ["2", "y"])          # delete screen number 2 (B)
    tracker.delete_transaction()
    fake_inputs(monkeypatch, ["2", "3", "999"])   # edit screen number 2, which is now C
    tracker.edit_transaction()
    amounts = {t.description: t.amount for t in tracker.load_transactions()}
    assert amounts == {"A": 100, "C": 999}


# ---------- display ----------

def test_format_transaction_expense():
    t = Transaction("expense", "Rice", 5000, "2026-10-04", "Food")
    assert tracker.format_transaction(2, t) == "2. 2026-10-04 | [expense] Rice | Food | ₦5,000.00"


def test_format_transaction_income_has_no_category():
    t = Transaction("income", "Salary", 200000, "2026-10-04")
    assert tracker.format_transaction(1, t) == "1. 2026-10-04 | [income] Salary | ₦200,000.00"


def test_view_transactions_when_empty(capsys):
    tracker.view_transactions()
    assert "No transactions yet." in capsys.readouterr().out


# ---------- keyword search ----------

def test_search_by_keyword_is_case_insensitive_and_keeps_numbers(monkeypatch, capsys):
    add("income", "Salary", 50000)
    add("expense", "Rice", 5000, "Food")
    add("expense", "Rice and chicken", 8500, "Food")
    fake_inputs(monkeypatch, ["RICE"])
    tracker.search_by_keyword()
    out = capsys.readouterr().out
    assert "2. " in out and "3. " in out
    assert "Salary" not in out


def test_search_by_keyword_matches_category(monkeypatch, capsys):
    add("expense", "Bus fare", 2000, "Transport")
    add("expense", "Rice", 5000, "Food")
    fake_inputs(monkeypatch, ["food"])
    tracker.search_by_keyword()
    out = capsys.readouterr().out
    assert "Rice" in out
    assert "Bus fare" not in out


def test_search_by_keyword_handles_income_without_category(monkeypatch, capsys):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["salary"])
    tracker.search_by_keyword()
    assert "Salary" in capsys.readouterr().out


def test_search_by_keyword_no_match(monkeypatch, capsys):
    add("income", "Salary", 50000)
    fake_inputs(monkeypatch, ["xyz"])
    tracker.search_by_keyword()
    assert "No transactions found" in capsys.readouterr().out

def test_statistics_monthly_summary(monkeypatch, capsys):
    add("income", "Salary", 50000, date="2026-10-01")
    add("expense", "Rice", 5000, "Food", date="2026-10-07")
    fake_inputs(monkeypatch, ["6"])
    tracker.show_statistics()
    out = capsys.readouterr().out
    assert "2026-10" in out
    assert "Income: ₦50,000.00" in out
    assert "Net: ₦45,000.00" in out