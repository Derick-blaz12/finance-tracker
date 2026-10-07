import json
import shutil

from models import Transaction

DATA_FILE = "transactions.json"


def save_transactions(transactions):
    """Overwrite the data file with the given list of Transaction objects."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in transactions], f, indent=2)

def _backup_data_file():
    """Copy the data file to DATA_FILE + '.bak' so skipped records aren't lost."""
    backup = DATA_FILE + ".bak"
    shutil.copyfile(DATA_FILE, backup)
    return backup


def load_transactions():
    """Return the valid saved transactions. Bad records are skipped with a warning."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []  # first run: no file yet
    except json.JSONDecodeError:
        print("Warning: data file is damaged. Starting with an empty list.")
        return []

    if not isinstance(data, list):
        backup = _backup_data_file()
        print(f"Warning: data file has the wrong format. Original saved as {backup}.")
        return []

    valid = []
    skipped = 0
    for record in data:
        try:
            valid.append(Transaction.from_dict(record))
        except (ValueError, TypeError):
            skipped += 1

    if skipped:
        backup = _backup_data_file()
        print(f"Warning: skipped {skipped} invalid record(s). Original saved as {backup}.")

    return valid