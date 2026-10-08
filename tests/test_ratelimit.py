import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

import ratelimit
from app import create_app


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    ratelimit.create_table(connection)
    yield connection
    connection.close()


def fail_n(conn, n, email="a@x.com", ip="1.1.1.1", now=None):
    for _ in range(n):
        ratelimit.record_failure(conn, email, ip, now)


def test_not_locked_below_the_limit(conn):
    fail_n(conn, 4)
    assert ratelimit.is_locked_out(conn, "a@x.com", "9.9.9.9") is False


def test_locked_by_email_at_the_limit(conn):
    fail_n(conn, 5, ip="1.1.1.1")
    assert ratelimit.is_locked_out(conn, "a@x.com", "8.8.8.8") is True


def test_locked_by_ip_across_different_emails(conn):
    for i in range(5):
        ratelimit.record_failure(conn, f"user{i}@x.com", "2.2.2.2")
    assert ratelimit.is_locked_out(conn, "fresh@x.com", "2.2.2.2") is True


def test_other_email_and_ip_unaffected(conn):
    fail_n(conn, 5)
    assert ratelimit.is_locked_out(conn, "other@x.com", "3.3.3.3") is False


def test_old_failures_expire(conn):
    old = datetime.now(timezone.utc) - timedelta(minutes=ratelimit.WINDOW_MINUTES + 1)
    fail_n(conn, 5, now=old)
    assert ratelimit.is_locked_out(conn, "a@x.com", "1.1.1.1") is False


def test_clear_failures_unlocks_the_email(conn):
    fail_n(conn, 5)
    ratelimit.clear_failures(conn, "a@x.com")
    assert ratelimit.is_locked_out(conn, "a@x.com", "9.9.9.9") is False


def test_purge_old_removes_only_expired_rows(conn):
    old = datetime.now(timezone.utc) - timedelta(minutes=ratelimit.WINDOW_MINUTES + 5)
    fail_n(conn, 3, now=old)
    fail_n(conn, 2)
    ratelimit.purge_old(conn)
    assert conn.execute("SELECT COUNT(*) FROM login_failures").fetchone()[0] == 2


# ---------- through the web app ----------

def make_app(tmp_path):
    return create_app(str(tmp_path / "rl.db"), secret_key="test-secret", csrf=False)


def attempt(client, password, email="ada@example.com"):
    return client.post("/login", data={"email": email, "password": password})


def test_five_wrong_passwords_then_lockout(tmp_path):
    app = make_app(tmp_path)
    app.test_client().post("/register", data={"email": "ada@example.com", "password": "correct horse"})
    client = app.test_client()
    for _ in range(5):
        assert attempt(client, "wrong").status_code == 400
    assert attempt(client, "wrong").status_code == 429


def test_correct_password_is_refused_while_locked_out(tmp_path):
    app = make_app(tmp_path)
    app.test_client().post("/register", data={"email": "ada@example.com", "password": "correct horse"})
    client = app.test_client()
    for _ in range(5):
        attempt(client, "wrong")
    response = attempt(client, "correct horse")
    assert response.status_code == 429
    assert client.get("/").status_code == 302   # still not logged in


def test_successful_login_clears_the_failures(tmp_path):
    app = make_app(tmp_path)
    app.test_client().post("/register", data={"email": "ada@example.com", "password": "correct horse"})
    client = app.test_client()
    for _ in range(4):
        attempt(client, "wrong")
    assert attempt(client, "correct horse").status_code == 302
    client.post("/logout")
    for _ in range(4):
        assert attempt(client, "wrong").status_code == 400


def test_lockout_message_is_the_same_for_unknown_emails(tmp_path):
    client = make_app(tmp_path).test_client()
    for _ in range(5):
        attempt(client, "x", email="ghost@example.com")
    response = attempt(client, "x", email="ghost@example.com")
    assert response.status_code == 429
    assert "Too many failed attempts" in response.get_data(as_text=True)