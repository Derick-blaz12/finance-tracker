from datetime import datetime, timedelta, timezone

MAX_FAILURES = 5
WINDOW_MINUTES = 15


def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS login_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            ip TEXT NOT NULL,
            at TEXT NOT NULL
        )
    """)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_login_failures_email ON login_failures(email, at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_login_failures_ip ON login_failures(ip, at)"
    )
    connection.commit()


def _now(now):
    return now or datetime.now(timezone.utc)


def _cutoff(now):
    return (_now(now) - timedelta(minutes=WINDOW_MINUTES)).isoformat(timespec="seconds")


def record_failure(connection, email, ip, now=None):
    connection.execute(
        "INSERT INTO login_failures (email, ip, at) VALUES (?, ?, ?)",
        (email, ip, _now(now).isoformat(timespec="seconds")),
    )
    connection.commit()


def is_locked_out(connection, email, ip, now=None):
    """True if this email or this IP has too many recent failures."""
    cutoff = _cutoff(now)
    by_email = connection.execute(
        "SELECT COUNT(*) FROM login_failures WHERE email = ? AND at >= ?",
        (email, cutoff),
    ).fetchone()[0]
    by_ip = connection.execute(
        "SELECT COUNT(*) FROM login_failures WHERE ip = ? AND at >= ?",
        (ip, cutoff),
    ).fetchone()[0]
    return by_email >= MAX_FAILURES or by_ip >= MAX_FAILURES


def clear_failures(connection, email):
    connection.execute("DELETE FROM login_failures WHERE email = ?", (email,))
    connection.commit()


def purge_old(connection, now=None):
    """Delete failures older than the window, so the table doesn't grow forever."""
    connection.execute("DELETE FROM login_failures WHERE at < ?", (_cutoff(now),))
    connection.commit()