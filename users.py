import sqlite3
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Used so a login attempt for an unknown email takes as long as a real one
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def create_users_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    connection.commit()


def normalize_email(email):
    return email.strip().lower()


def validate_email(email):
    """Raise ValueError unless email looks like name@domain.tld."""
    local, separator, domain = email.partition("@")
    looks_valid = (
        separator
        and local
        and "." in domain
        and not domain.startswith(".")
        and not domain.endswith(".")
        and "@" not in domain
        and " " not in email
        and len(email) <= 254
    )
    if not looks_valid:
        raise ValueError("Enter a valid email address.")


def validate_password(password):
    """Raise ValueError if the password is too short or too long."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.")


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def create_user(connection, email, password):
    """Create an account and return its id. Raises ValueError if invalid or taken."""
    email = normalize_email(email)
    validate_email(email)
    validate_password(password)
    try:
        cursor = connection.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (
                email,
                hash_password(password),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
    except sqlite3.IntegrityError:
        raise ValueError("An account with this email already exists.")
    connection.commit()
    return cursor.lastrowid


def get_user_by_email(connection, email):
    """Return (id, email), or None if there is no such user."""
    return connection.execute(
        "SELECT id, email FROM users WHERE email = ?", (normalize_email(email),)
    ).fetchone()


def get_user_by_id(connection, user_id):
    """Return (id, email), or None if there is no such user."""
    return connection.execute(
        "SELECT id, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def authenticate(connection, email, password):
    """Return the user's id if the email and password match, otherwise None."""
    row = connection.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
        (normalize_email(email),),
    ).fetchone()
    if row is None:
        check_password_hash(_DUMMY_HASH, password)   # keep timing similar
        return None
    user_id, password_hash = row
    if check_password_hash(password_hash, password):
        return user_id
    return None