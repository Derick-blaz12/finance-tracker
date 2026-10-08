import sqlite3

import pytest

import database
from models import Transaction

A = 1   # one user
B = 2   # another user


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
    assert database.add_transaction(conn, A, expense()) == 1
    assert database.add_transaction(conn, A, expense("Bus fare", 2000, "Transport")) == 2


def test_get_all_when_empty(conn):
    assert database.get_all_transactions(conn, A) == []


def test_expense_round_trip(conn):
    t = expense()
    new_id = database.add_transaction(conn, A, t)
    assert database.get_all_transactions(conn, A) == [(new_id, t)]


def test_income_comes_back_with_no_category(conn):
    database.add_transaction(conn, A, income())
    (_, t), = database.get_all_transactions(conn, A)
    assert t.category is None


def test_delete_removes_the_row(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.delete_transaction(conn, A, new_id) is True
    assert database.get_all_transactions(conn, A) == []


def test_delete_missing_id_returns_false(conn):
    assert database.delete_transaction(conn, A, 999) is False


def test_ids_do_not_shift_after_delete(conn):
    database.add_transaction(conn, A, expense("A"))
    database.add_transaction(conn, A, expense("B"))
    database.add_transaction(conn, A, expense("C"))
    database.delete_transaction(conn, A, 2)
    ids = [row_id for row_id, t in database.get_all_transactions(conn, A)]
    assert ids == [1, 3]


def test_update_changes_one_field_only(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.update_transaction(conn, A, new_id, "amount", 6500) is True
    (_, t), = database.get_all_transactions(conn, A)
    assert t.amount == 6500
    assert t.description == "Rice"


def test_update_missing_id_returns_false(conn):
    assert database.update_transaction(conn, A, 999, "amount", 100) is False


def test_invalid_update_raises_and_leaves_row_unchanged(conn):
    new_id = database.add_transaction(conn, A, expense())
    with pytest.raises(ValueError):
        database.update_transaction(conn, A, new_id, "amount", -10)
    (_, t), = database.get_all_transactions(conn, A)
    assert t.amount == 5000


def test_update_category_on_income_raises(conn):
    new_id = database.add_transaction(conn, A, income())
    with pytest.raises(ValueError):
        database.update_transaction(conn, A, new_id, "category", "Food")
    (_, t), = database.get_all_transactions(conn, A)
    assert t.category is None


def test_update_unknown_field_raises(conn):
    new_id = database.add_transaction(conn, A, expense())
    with pytest.raises(ValueError):
        database.update_transaction(conn, A, new_id, "ammount", 1)


def test_amount_comes_back_as_int(conn):
    database.add_transaction(conn, A, expense(amount=500050))
    (_, t), = database.get_all_transactions(conn, A)
    assert t.amount == 500050
    assert isinstance(t.amount, int)


def test_get_transaction_by_id(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.get_transaction(conn, A, new_id) == expense()
    assert database.get_transaction(conn, A, 999) is None


def test_replace_transaction_overwrites_all_fields(conn):
    new_id = database.add_transaction(conn, A, expense())
    replacement = Transaction("income", "Gift", 700, "2026-10-05")
    assert database.replace_transaction(conn, A, new_id, replacement) is True
    assert database.get_transaction(conn, A, new_id) == replacement
    assert database.replace_transaction(conn, A, 999, replacement) is False


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
    assert database.get_all_transactions(old, A) == []        # unowned rows are hidden
    database.assign_unowned_transactions(old, A)
    assert len(database.get_all_transactions(old, A)) == 1    # now they belong to A


def test_ensure_user_id_column_twice_is_fine(conn):
    database.ensure_user_id_column(conn)
    database.ensure_user_id_column(conn)


def test_assign_unowned_only_touches_rows_without_an_owner(conn):
    conn.execute(
        "INSERT INTO transactions (type, description, amount, date, category, user_id) "
        "VALUES ('expense', 'Unowned', 100, '2026-10-04', 'Food', NULL)"
    )
    conn.commit()
    database.add_transaction(conn, B, expense("Owned"))

    assert database.assign_unowned_transactions(conn, A) == 1
    owners = dict(conn.execute("SELECT description, user_id FROM transactions"))
    assert owners == {"Unowned": A, "Owned": B}


def test_assign_unowned_returns_zero_when_nothing_to_assign(conn):
    assert database.assign_unowned_transactions(conn, A) == 0


# ---------- isolation between users ----------

def test_get_all_only_returns_own_transactions(conn):
    database.add_transaction(conn, A, expense("Mine"))
    database.add_transaction(conn, B, expense("Theirs"))
    assert [t.description for _, t in database.get_all_transactions(conn, A)] == ["Mine"]
    assert [t.description for _, t in database.get_all_transactions(conn, B)] == ["Theirs"]


def test_get_transaction_of_another_user_is_none(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.get_transaction(conn, B, new_id) is None


def test_update_another_users_transaction_fails(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.update_transaction(conn, B, new_id, "amount", 1) is False
    assert database.get_transaction(conn, A, new_id).amount == 5000


def test_replace_another_users_transaction_fails(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.replace_transaction(conn, B, new_id, income("Hijack", 1)) is False
    assert database.get_transaction(conn, A, new_id) == expense()


def test_delete_another_users_transaction_fails(conn):
    new_id = database.add_transaction(conn, A, expense())
    assert database.delete_transaction(conn, B, new_id) is False
    assert database.get_transaction(conn, A, new_id) is not None


def test_user_id_is_required(conn):
    with pytest.raises(TypeError):
        database.get_all_transactions(conn)