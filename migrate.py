import database
import storage


def import_transactions(connection, transactions):
    """Copy Transaction objects into an EMPTY database. Returns how many were imported.

    If the database already has rows, nothing is imported and 0 is returned,
    so running this twice can't create duplicates.
    """
    existing = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    if existing > 0:
        return 0

    connection.executemany(
        "INSERT INTO transactions (type, description, amount, date, category) "
        "VALUES (?, ?, ?, ?, ?)",
        [(t.type, t.description, t.amount, t.date, t.category) for t in transactions],
    )
    connection.commit()   # one commit: either every row goes in, or none do
    return len(transactions)


def main():
    transactions = storage.load_transactions()
    connection = database.connect()
    database.create_table(connection)
    count = import_transactions(connection, transactions)
    connection.close()

    if count:
        print(f"Imported {count} transaction(s) into {database.DB_FILE}.")
    else:
        print("Nothing imported (the database already has data, or the JSON file is empty).")


if __name__ == "__main__":
    main()