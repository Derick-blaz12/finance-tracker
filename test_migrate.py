import sqlite3

import pytest

import database
import migrate
from models import Transaction


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    database.create_table(connection)
    yield connection
    connection.close()


def sample():
    return [
        Transaction("income", "Salary", 50000, "2026-10-04"),
        Transaction("expense", "Rice", 5000, "2026-10-04", "Food"),
    ]


def test_import_into_empty_database(conn):
    data = sample()
    assert migrate.import_transactions(conn, data) == 2
    assert [t for _, t in database.get_all_transactions(conn)] == data


def test_import_assigns_ids_in_order(conn):
    migrate.import_transactions(conn, sample())
    ids = [row_id for row_id, _ in database.get_all_transactions(conn)]
    assert ids == [1, 2]


def test_second_import_adds_nothing(conn):
    migrate.import_transactions(conn, sample())
    assert migrate.import_transactions(conn, sample()) == 0
    assert len(database.get_all_transactions(conn)) == 2


def test_import_skipped_when_database_already_has_data(conn):
    database.add_transaction(conn, Transaction("income", "Existing", 1, "2026-10-04"))
    assert migrate.import_transactions(conn, sample()) == 0
    assert len(database.get_all_transactions(conn)) == 1


def test_import_empty_list(conn):
    assert migrate.import_transactions(conn, []) == 0
    assert database.get_all_transactions(conn) == []