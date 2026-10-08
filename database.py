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
            amount INTEGER NOT NULL,
            date TEXT NOT NULL,
            category TEXT,
            user_id INTEGER
        )
    """)
    connection.commit()
    ensure_user_id_column(connection)


def ensure_user_id_column(connection):
    """Add the user_id column to an older table. Safe to run repeatedly."""
    columns = [row[1] for row in connection.execute("PRAGMA table_info(transactions)")]
    if "user_id" not in columns:
        connection.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)"
    )
    connection.commit()


def assign_unowned_transactions(connection, user_id):
    """Give every transaction that has no owner to this user. Returns how many."""
    cursor = connection.execute(
        "UPDATE transactions SET user_id = ? WHERE user_id IS NULL", (user_id,)
    )
    connection.commit()
    return cursor.rowcount


def add_transaction(connection, user_id, t):
    """Insert a Transaction owned by user_id and return its new id."""
    cursor = connection.execute(
        "INSERT INTO transactions (type, description, amount, date, category, user_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (t.type, t.description, t.amount, t.date, t.category, user_id),
    )
    connection.commit()
    return cursor.lastrowid


def get_all_transactions(connection, user_id):
    """Return a list of (id, Transaction) pairs for this user, oldest id first."""
    rows = connection.execute(
        "SELECT id, type, description, amount, date, category "
        "FROM transactions WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    return [
        (row[0], Transaction.from_dict(dict(zip(COLUMNS, row[1:]))))
        for row in rows
    ]


def get_transaction(connection, user_id, transaction_id):
    """Return this user's Transaction with this id, or None if there isn't one."""
    row = connection.execute(
        "SELECT type, description, amount, date, category "
        "FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    ).fetchone()
    if row is None:
        return None
    return Transaction.from_dict(dict(zip(COLUMNS, row)))


def update_transaction(connection, user_id, transaction_id, field, value):
    """Change one field. Returns False if this user has no such transaction.

    Raises ValueError if the field can't be edited or the new value is invalid.
    The row is only written if the changed transaction passes validation.
    """
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"Cannot edit field '{field}'.")

    row = connection.execute(
        "SELECT type, description, amount, date, category "
        "FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    ).fetchone()
    if row is None:
        return False

    changed = dict(zip(COLUMNS, row))
    changed[field] = value
    t = Transaction.from_dict(changed)   # validates; raises ValueError if bad

    connection.execute(
        "UPDATE transactions "
        "SET type = ?, description = ?, amount = ?, date = ?, category = ? "
        "WHERE id = ? AND user_id = ?",
        (t.type, t.description, t.amount, t.date, t.category, transaction_id, user_id),
    )
    connection.commit()
    return True


def replace_transaction(connection, user_id, transaction_id, t):
    """Overwrite every field of this user's row with a validated Transaction.

    Returns False if this user has no such transaction.
    """
    cursor = connection.execute(
        "UPDATE transactions "
        "SET type = ?, description = ?, amount = ?, date = ?, category = ? "
        "WHERE id = ? AND user_id = ?",
        (t.type, t.description, t.amount, t.date, t.category, transaction_id, user_id),
    )
    connection.commit()
    return cursor.rowcount == 1


def delete_transaction(connection, user_id, transaction_id):
    """Delete this user's transaction. Returns True if a row was deleted."""
    cursor = connection.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    )
    connection.commit()
    return cursor.rowcount == 1