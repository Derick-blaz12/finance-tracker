import sqlite3

from models import Transaction

DB_FILE = "finance.db"
EDITABLE_FIELDS = ("description", "amount", "date", "category")
COLUMNS = ("type", "description", "amount", "date", "category")


def connect():
    """Open a connection to the real database file."""
    return sqlite3.connect(DB_FILE)


def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            category TEXT
        )
    """)
    connection.commit()


def add_transaction(connection, t):
    """Insert a Transaction and return its new id."""
    cursor = connection.execute(
        "INSERT INTO transactions (type, description, amount, date, category) "
        "VALUES (?, ?, ?, ?, ?)",
        (t.type, t.description, t.amount, t.date, t.category),
    )
    connection.commit()
    return cursor.lastrowid


def get_all_transactions(connection):
    """Return a list of (id, Transaction) pairs, oldest id first."""
    rows = connection.execute(
        "SELECT id, type, description, amount, date, category "
        "FROM transactions ORDER BY id"
    ).fetchall()
    return [
        (row[0], Transaction.from_dict(dict(zip(COLUMNS, row[1:]))))
        for row in rows
    ]


def update_transaction(connection, transaction_id, field, value):
    """Change one field. Returns False if the id doesn't exist.

    Raises ValueError if the field can't be edited or the new value is invalid.
    The row is only written if the changed transaction passes validation.
    """
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"Cannot edit field '{field}'.")

    row = connection.execute(
        "SELECT type, description, amount, date, category "
        "FROM transactions WHERE id = ?",
        (transaction_id,),
    ).fetchone()
    if row is None:
        return False

    changed = dict(zip(COLUMNS, row))
    changed[field] = value
    t = Transaction.from_dict(changed)   # validates; raises ValueError if bad

    connection.execute(
        "UPDATE transactions "
        "SET type = ?, description = ?, amount = ?, date = ?, category = ? "
        "WHERE id = ?",
        (t.type, t.description, t.amount, t.date, t.category, transaction_id),
    )
    connection.commit()
    return True


def delete_transaction(connection, transaction_id):
    """Delete by id. Returns True if a row was deleted, False if none matched."""
    cursor = connection.execute(
        "DELETE FROM transactions WHERE id = ?", (transaction_id,)
    )
    connection.commit()
    return cursor.rowcount == 1