import sqlite3

import database
from app import create_app
from models import Transaction


def make_client(tmp_path, transactions=()):
    db_file = str(tmp_path / "test_web.db")
    conn = sqlite3.connect(db_file)
    database.create_table(conn)
    for t in transactions:
        database.add_transaction(conn, t)
    conn.close()
    return create_app(db_file).test_client()


def test_dashboard_shows_totals(tmp_path):
    client = make_client(tmp_path, [
        Transaction("income", "Salary", 5000000, "2026-10-01"),
        Transaction("expense", "Rice", 500050, "2026-10-02", "Food"),
    ])
    html = client.get("/").get_data(as_text=True)
    assert "₦50,000.00" in html    # income
    assert "₦5,000.50" in html     # expenses
    assert "₦44,999.50" in html    # balance


def test_dashboard_with_empty_database(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "₦0.00" in response.get_data(as_text=True)