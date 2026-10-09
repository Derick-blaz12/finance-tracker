import os
import sqlite3

import pytest

import backup
import database
import users
from app import create_app


def test_security_headers_on_every_response(tmp_path):
    client = create_app(str(tmp_path / "h.db"), secret_key="k", csrf=False).test_client()
    for url in ["/login", "/no-such-page"]:
        headers = client.get(url).headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["Referrer-Policy"] == "same-origin"


def test_production_refuses_a_missing_database_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("PRODUCTION", "1")
    missing = str(tmp_path / "no-such-disk" / "finance.db")
    with pytest.raises(RuntimeError, match="does not exist"):
        create_app(missing, secret_key="k")


def test_production_accepts_an_existing_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("PRODUCTION", "1")
    create_app(str(tmp_path / "finance.db"), secret_key="k")


def make_source(tmp_path):
    path = str(tmp_path / "source.db")
    conn = sqlite3.connect(path)
    database.create_table(conn)
    users.create_users_table(conn)
    users.create_user(conn, "ada@example.com", "correct horse")
    conn.close()
    return path


def test_backup_can_be_restored_with_accounts_intact(tmp_path):
    source = make_source(tmp_path)
    target = backup.backup_database(source, str(tmp_path / "backups"))
    restored = sqlite3.connect(target)
    assert users.authenticate(restored, "ada@example.com", "correct horse") == 1
    restored.close()


def test_backup_keeps_only_the_newest_files(tmp_path):
    source = make_source(tmp_path)
    folder = tmp_path / "backups"
    folder.mkdir()
    for i in range(5):
        (folder / f"finance-2000010{i}-000000.db").write_bytes(b"old")
    backup.backup_database(source, str(folder), keep=3)
    assert len(os.listdir(folder)) == 3