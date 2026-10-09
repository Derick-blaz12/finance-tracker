import sqlite3

import database
import export
import ratelimit
from app import create_app
from models import Transaction


def make_app(tmp_path):
    return create_app(str(tmp_path / "acc.db"), secret_key="test-secret", csrf=False)


def sign_up(app, email, password="correct horse"):
    client = app.test_client()
    client.post("/register", data={"email": email, "password": password})
    return client


def add_expense(client, description="Rice", amount="123.45"):
    client.post("/transactions/new", data={
        "type": "expense", "description": description, "category": "Food",
        "amount": amount, "date": "2026-10-07",
    })


def count(tmp_path, table):
    conn = sqlite3.connect(str(tmp_path / "acc.db"))
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return n


# ---------- export ----------

def test_csv_contains_own_transactions_with_plain_decimals(tmp_path):
    client = sign_up(make_app(tmp_path), "ada@example.com")
    add_expense(client, "Rice", "1,234.56")
    response = client.get("/export.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    body = response.get_data(as_text=True)
    assert "date,type,description,category,amount_naira" in body
    assert "2026-10-07,expense,Rice,Food,1234.56" in body


def test_csv_never_includes_another_users_data(tmp_path):
    app = make_app(tmp_path)
    ada = sign_up(app, "ada@example.com")
    grace = sign_up(app, "grace@example.com", "another horse")
    add_expense(ada, "Ada secret")
    assert "Ada secret" not in grace.get("/export.csv").get_data(as_text=True)


def test_csv_neutralises_formulas():
    row = Transaction("expense", "=HYPERLINK(\"x\")", 100, "2026-10-07", "Food")
    body = export.transactions_to_csv([(1, row)])
    assert "'=HYPERLINK" in body


def test_kobo_to_decimal():
    assert export.kobo_to_decimal(500050) == "5000.50"
    assert export.kobo_to_decimal(5) == "0.05"


# ---------- deletion ----------

def test_wrong_password_deletes_nothing(tmp_path):
    client = sign_up(make_app(tmp_path), "ada@example.com")
    add_expense(client)
    response = client.post("/account/delete", data={"password": "wrong"})
    assert response.status_code == 400
    assert count(tmp_path, "users") == 1
    assert count(tmp_path, "transactions") == 1


def test_delete_removes_account_and_transactions_and_logs_out(tmp_path):
    client = sign_up(make_app(tmp_path), "ada@example.com")
    add_expense(client)
    response = client.post("/account/delete", data={"password": "correct horse"})
    assert response.status_code == 302
    assert count(tmp_path, "users") == 0
    assert count(tmp_path, "transactions") == 0
    assert client.get("/").status_code == 302


def test_delete_leaves_other_users_untouched(tmp_path):
    app = make_app(tmp_path)
    ada = sign_up(app, "ada@example.com")
    grace = sign_up(app, "grace@example.com", "another horse")
    add_expense(ada, "Ada item")
    add_expense(grace, "Grace item")
    ada.post("/account/delete", data={"password": "correct horse"})
    assert count(tmp_path, "users") == 1
    assert "Grace item" in grace.get("/transactions").get_data(as_text=True)


def test_deleted_email_can_register_again_with_a_clean_slate(tmp_path):
    app = make_app(tmp_path)
    client = sign_up(app, "ada@example.com")
    add_expense(client)
    client.post("/account/delete", data={"password": "correct horse"})
    again = sign_up(app, "ada@example.com")
    assert "No transactions yet." in again.get("/transactions").get_data(as_text=True)


def test_repeated_wrong_passwords_lock_out_deletion(tmp_path):
    client = sign_up(make_app(tmp_path), "ada@example.com")
    for _ in range(ratelimit.MAX_FAILURES):
        client.post("/account/delete", data={"password": "wrong"})
    response = client.post("/account/delete", data={"password": "correct horse"})
    assert response.status_code == 429
    assert count(tmp_path, "users") == 1


def test_delete_user_data_rolls_back_on_failure():
    conn = sqlite3.connect(":memory:")
    database.create_table(conn)
    database.add_transaction(conn, 1, Transaction("income", "Salary", 100, "2026-10-01"))
    # no users or login_failures table, so the later DELETEs fail
    try:
        database.delete_user_data(conn, 1, "a@x.com")
    except sqlite3.OperationalError:
        pass
    assert len(database.get_all_transactions(conn, 1)) == 1