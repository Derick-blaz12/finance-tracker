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

def convert_amounts_to_kobo(connection):
    """Rebuild the table with INTEGER amounts, multiplying old values by 100.

    Returns the number of rows converted, or 0 if already converted.
    """
    columns = connection.execute("PRAGMA table_info(transactions)").fetchall()
    amount_type = next(c[2] for c in columns if c[1] == "amount")
    if amount_type.upper() == "INTEGER":
        return 0

    count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    connection.executescript("""
        BEGIN;
        CREATE TABLE transactions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            amount INTEGER NOT NULL,
            date TEXT NOT NULL,
            category TEXT
        );
        INSERT INTO transactions_new (id, type, description, amount, date, category)
            SELECT id, type, description, CAST(ROUND(amount * 100) AS INTEGER), date, category
            FROM transactions;
        DROP TABLE transactions;
        ALTER TABLE transactions_new RENAME TO transactions;
        COMMIT;
    """)
    return count

def replace_transaction(connection, transaction_id, t):
    """Overwrite every field of a row with a validated Transaction.

    Returns False if the id doesn't exist.
    """
    cursor = connection.execute(
        "UPDATE transactions "
        "SET type = ?, description = ?, amount = ?, date = ?, category = ? "
        "WHERE id = ?",
        (t.type, t.description, t.amount, t.date, t.category, transaction_id),
    )
    connection.commit()
    return cursor.rowcount == 1

def get_transaction(connection, transaction_id):
    """Return the Transaction with this id, or None if it doesn't exist."""
    row = connection.execute(
        "SELECT type, description, amount, date, category "
        "FROM transactions WHERE id = ?",
        (transaction_id,),
    ).fetchone()
    if row is None:
        return None
    return Transaction.from_dict(dict(zip(COLUMNS, row)))

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