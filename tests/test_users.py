import sqlite3

import pytest

import users


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    users.create_users_table(connection)
    yield connection
    connection.close()


def test_hash_is_not_the_password():
    assert users.hash_password("correct horse") != "correct horse"


def test_same_password_hashes_differently_each_time():
    assert users.hash_password("correct horse") != users.hash_password("correct horse")


def test_verify_correct_and_wrong_password():
    hashed = users.hash_password("correct horse")
    assert users.verify_password(hashed, "correct horse") is True
    assert users.verify_password(hashed, "wrong horse") is False


def test_create_users_table_twice_is_fine(conn):
    users.create_users_table(conn)


def test_create_user_returns_id_and_lowercases_email(conn):
    user_id = users.create_user(conn, "  Ada@Example.COM ", "correct horse")
    assert user_id == 1
    assert users.get_user_by_id(conn, user_id) == (1, "ada@example.com")


def test_duplicate_email_rejected_ignoring_case(conn):
    users.create_user(conn, "ada@example.com", "correct horse")
    with pytest.raises(ValueError, match="already exists"):
        users.create_user(conn, "ADA@example.com", "another password")


def test_short_password_rejected(conn):
    with pytest.raises(ValueError):
        users.create_user(conn, "ada@example.com", "short")
    assert users.get_user_by_email(conn, "ada@example.com") is None


def test_too_long_password_rejected(conn):
    with pytest.raises(ValueError):
        users.create_user(conn, "ada@example.com", "x" * 129)


@pytest.mark.parametrize("bad", ["", "abc", "a@b", "@x.com", "a b@x.com", "a@@x.com"])
def test_invalid_emails_rejected(conn, bad):
    with pytest.raises(ValueError):
        users.create_user(conn, bad, "correct horse")


def test_get_user_by_email_ignores_case(conn):
    users.create_user(conn, "ada@example.com", "correct horse")
    assert users.get_user_by_email(conn, "Ada@Example.com") == (1, "ada@example.com")


def test_get_user_by_id_and_missing(conn):
    user_id = users.create_user(conn, "ada@example.com", "correct horse")
    assert users.get_user_by_id(conn, user_id) == (user_id, "ada@example.com")
    assert users.get_user_by_id(conn, 999) is None


def test_authenticate_success(conn):
    user_id = users.create_user(conn, "ada@example.com", "correct horse")
    assert users.authenticate(conn, "ADA@example.com", "correct horse") == user_id


def test_authenticate_failures_return_none(conn):
    users.create_user(conn, "ada@example.com", "correct horse")
    assert users.authenticate(conn, "ada@example.com", "wrong horse") is None
    assert users.authenticate(conn, "nobody@example.com", "correct horse") is None


def test_password_is_not_stored_in_plain_text(conn):
    users.create_user(conn, "ada@example.com", "correct horse")
    stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "correct horse" not in stored