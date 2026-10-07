import sqlite3

import pytest

import database
from models import Transaction


@pytest.fixture
def conn():
    """A fresh in-memory database for each test. Nothing touches finance.db."""
    connection = sqlite3.connect(":memory:")
    database.create_table(connection)
    yield connection
    connection.close()


def expense(description="Rice", amount=5000, category="Food"):
    return Transaction("expense", description, amount, "2026-10-04", category)


def income(description="Salary", amount=50000):
    return Transaction("income", description, amount, "2026-10-04")


def test_create_table_twice_is_fine(conn):
    database.create_table(conn)   # the fixture already created it once


def test_add_returns_new_ids(conn):
    assert database.add_transaction(conn, expense()) == 1
    assert database.add_transaction(conn, expense("Bus fare", 2000, "Transport")) == 2


def test_get_all_when_empty(conn):
    assert database.get_all_transactions(conn) == []


def test_expense_round_trip(conn):
    t = expense()
    new_id = database.add_transaction(conn, t)
    assert database.get_all_transactions(conn) == [(new_id, t)]


def test_income_comes_back_with_no_category(conn):
    database.add_transaction(conn, income())
    (_, t), = database.get_all_transactions(conn)
    assert t.category is None


def test_delete_removes_the_row(conn):
    new_id = database.add_transaction(conn, expense())
    assert database.delete_transaction(conn, new_id) is True
    assert database.get_all_transactions(conn) == []


def test_delete_missing_id_returns_false(conn):
    assert database.delete_transaction(conn, 999) is False


def test_ids_do_not_shift_after_delete(conn):
    database.add_transaction(conn, expense("A"))
    database.add_transaction(conn, expense("B"))
    database.add_transaction(conn, expense("C"))
    database.delete_transaction(conn, 2)
    ids = [row_id for row_id, t in database.get_all_transactions(conn)]
    assert ids == [1, 3]


def test_update_changes_one_field_only(conn):
    new_id = database.add_transaction(conn, expense())
    assert database.update_transaction(conn, new_id, "amount", 6500) is True
    (_, t), = database.get_all_transactions(conn)
    assert t.amount == 6500
    assert t.description == "Rice"


def test_update_missing_id_returns_false(conn):
    assert database.update_transaction(conn, 999, "amount", 100) is False


def test_invalid_update_raises_and_leaves_row_unchanged(conn):
    new_id = database.add_transaction(conn, expense())
    with pytest.raises(ValueError):
        database.update_transaction(conn, new_id, "amount", -10)
    (_, t), = database.get_all_transactions(conn)
    assert t.amount == 5000


def test_update_category_on_income_raises(conn):
    new_id = database.add_transaction(conn, income())
    with pytest.raises(ValueError):
        database.update_transaction(conn, new_id, "category", "Food")
    (_, t), = database.get_all_transactions(conn)
    assert t.category is None


def test_update_unknown_field_raises(conn):
    new_id = database.add_transaction(conn, expense())
    with pytest.raises(ValueError):
        database.update_transaction(conn, new_id, "ammount", 1)