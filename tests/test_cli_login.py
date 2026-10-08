import sqlite3

import pytest

import main
import users


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    users.create_users_table(connection)
    users.create_user(connection, "ada@example.com", "correct horse")
    yield connection
    connection.close()


def fake_login(monkeypatch, emails, passwords):
    emails, passwords = iter(emails), iter(passwords)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(emails))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(passwords))


def test_log_in_success(monkeypatch, conn):
    fake_login(monkeypatch, ["ada@example.com"], ["correct horse"])
    assert main.log_in(conn) == 1


def test_log_in_gives_up_after_three_failures(monkeypatch, conn, capsys):
    fake_login(monkeypatch, ["ada@example.com"] * 3, ["wrong"] * 3)
    assert main.log_in(conn) is None
    assert capsys.readouterr().out.count("Incorrect email or password.") == 3