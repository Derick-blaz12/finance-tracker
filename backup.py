import os
import sqlite3
import sys
from datetime import datetime, timezone


def backup_database(source_file, backup_folder, keep=14):
    """Copy the database with SQLite's online backup. Returns the new file's path.

    Keeps only the newest `keep` backups in the folder.
    """
    os.makedirs(backup_folder, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = os.path.join(backup_folder, f"finance-{stamp}.db")

    source = sqlite3.connect(source_file)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    old = sorted(f for f in os.listdir(backup_folder) if f.startswith("finance-"))
    for name in old[:-keep]:
        os.remove(os.path.join(backup_folder, name))
    return target


if __name__ == "__main__":
    source = os.environ.get("DATABASE_FILE", "finance.db")
    folder = sys.argv[1] if len(sys.argv) > 1 else "backups"
    print("Backup written to", backup_database(source, folder))