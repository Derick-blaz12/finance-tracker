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

def test_amount_comes_back_as_int(conn):
    database.add_transaction(conn, expense(amount=500050))
    (_, t), = database.get_all_transactions(conn)
    assert t.amount == 500050
    assert isinstance(t.amount, int)


def test_convert_old_real_table_to_kobo():
    old = sqlite3.connect(":memory:")
    old.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
        description TEXT NOT NULL, amount REAL NOT NULL,
        date TEXT NOT NULL, category TEXT)""")
    old.execute("INSERT INTO transactions (type, description, amount, date, category) "
                "VALUES ('expense', 'Rice', 5000.5, '2026-10-04', 'Food')")
    old.execute("INSERT INTO transactions (type, description, amount, date) "
                "VALUES ('income', 'Salary', 200000.0, '2026-10-04')")
    old.commit()

    assert database.convert_amounts_to_kobo(old) == 2
    amounts = [t.amount for _, t in database.get_all_transactions(old)]
    assert amounts == [500050, 20000000]
    assert all(isinstance(a, int) for a in amounts)


def test_convert_twice_does_nothing(conn):
    assert database.convert_amounts_to_kobo(conn) == 0

def test_get_transaction_by_id(conn):
    new_id = database.add_transaction(conn, expense())
    assert database.get_transaction(conn, new_id) == expense()
    assert database.get_transaction(conn, 999) is None


def test_replace_transaction_overwrites_all_fields(conn):
    new_id = database.add_transaction(conn, expense())
    replacement = Transaction("income", "Gift", 700, "2026-10-05")
    assert database.replace_transaction(conn, new_id, replacement) is True
    assert database.get_transaction(conn, new_id) == replacement
    assert database.replace_transaction(conn, 999, replacement) is False

def user_id_column_exists(connection):
    return "user_id" in [r[1] for r in connection.execute("PRAGMA table_info(transactions)")]


def test_new_table_has_user_id_column(conn):
    assert user_id_column_exists(conn)


def test_ensure_adds_column_to_an_old_table():
    old = sqlite3.connect(":memory:")
    old.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
        description TEXT NOT NULL, amount INTEGER NOT NULL,
        date TEXT NOT NULL, category TEXT)""")
    old.execute("INSERT INTO transactions (type, description, amount, date) "
                "VALUES ('income', 'Salary', 100, '2026-10-01')")
    old.commit()
    assert not user_id_column_exists(old)

    database.ensure_user_id_column(old)

    assert user_id_column_exists(old)
    assert old.execute("SELECT user_id FROM transactions").fetchone() == (None,)
    assert len(database.get_all_transactions(old)) == 1   # existing data still readable


def test_ensure_user_id_column_twice_is_fine(conn):
    database.ensure_user_id_column(conn)
    database.ensure_user_id_column(conn)


def test_assign_unowned_only_touches_rows_without_an_owner(conn):
    first = database.add_transaction(conn, expense("A"))
    database.add_transaction(conn, expense("B"))
    conn.execute("UPDATE transactions SET user_id = 2 WHERE id = ?", (first,))
    conn.commit()

    assert database.assign_unowned_transactions(conn, 1) == 1
    owners = dict(conn.execute("SELECT id, user_id FROM transactions"))
    assert owners[first] == 2          # kept its owner
    assert owners[first + 1] == 1      # was unowned, now assigned


def test_assign_unowned_returns_zero_when_nothing_to_assign(conn):
    assert database.assign_unowned_transactions(conn, 1) == 0