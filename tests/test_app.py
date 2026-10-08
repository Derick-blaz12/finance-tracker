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

def test_transactions_page_lists_newest_first(tmp_path):
    client = make_client(tmp_path, [
        Transaction("income", "Salary", 5000000, "2026-10-01"),
        Transaction("expense", "Rice", 500050, "2026-10-07", "Food"),
    ])
    html = client.get("/transactions").get_data(as_text=True)
    assert html.index("Rice") < html.index("Salary")
    assert "₦5,000.50" in html
    assert "Food" in html


def test_transactions_page_empty(tmp_path):
    client = make_client(tmp_path)
    html = client.get("/transactions").get_data(as_text=True)
    assert "No transactions yet." in html


def test_descriptions_are_escaped(tmp_path):
    client = make_client(tmp_path, [
        Transaction("expense", "<b>bold</b>", 100, "2026-10-01", "Other"),
    ])
    html = client.get("/transactions").get_data(as_text=True)
    assert "<b>bold</b>" not in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html

def test_new_transaction_form_loads(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/transactions/new")
    assert response.status_code == 200
    assert "Add transaction" in response.get_data(as_text=True)


def test_valid_expense_is_saved_in_kobo(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "food",
        "amount": "1,234.56", "date": "2026-10-07",
    })
    assert response.status_code == 302            # redirected after success
    html = client.get("/transactions").get_data(as_text=True)
    assert "Rice" in html
    assert "Food" in html                          # title-cased like the CLI
    assert "₦1,234.56" in html


def test_income_ignores_category(tmp_path):
    client = make_client(tmp_path)
    client.post("/transactions/new", data={
        "type": "income", "description": "Salary", "category": "Food",
        "amount": "50000", "date": "2026-10-01",
    })
    html = client.get("/transactions").get_data(as_text=True)
    assert "Salary" in html
    assert "Food" not in html


def test_invalid_amount_is_rejected_and_nothing_saved(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "Food",
        "amount": "1.234", "date": "2026-10-07",
    })
    assert response.status_code == 400
    assert "Amount must be a number" in response.get_data(as_text=True)
    assert "No transactions yet." in client.get("/transactions").get_data(as_text=True)


def test_future_date_is_rejected(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "Food",
        "amount": "100", "date": "2999-01-01",
    })
    assert response.status_code == 400
    assert "future" in response.get_data(as_text=True)


def test_expense_without_category_is_rejected(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "",
        "amount": "100", "date": "2026-10-07",
    })
    assert response.status_code == 400
    assert "Expenses need a category" in response.get_data(as_text=True)


def test_form_keeps_values_after_an_error(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice and chicken", "category": "Food",
        "amount": "abc", "date": "2026-10-07",
    })
    assert 'value="Rice and chicken"' in response.get_data(as_text=True)

def first_id(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "test_web.db"))
    row_id = database.get_all_transactions(conn)[0][0]
    conn.close()
    return row_id


def test_delete_removes_the_transaction(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 500, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    response = client.post(f"/transactions/{row_id}/delete")
    assert response.status_code == 302
    assert "No transactions yet." in client.get("/transactions").get_data(as_text=True)


def test_delete_missing_id_is_404(tmp_path):
    client = make_client(tmp_path)
    assert client.post("/transactions/999/delete").status_code == 404


def test_delete_by_get_is_not_allowed(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 500, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    assert client.get(f"/transactions/{row_id}/delete").status_code == 405


def test_edit_form_is_prefilled(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 123456, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    html = client.get(f"/transactions/{row_id}/edit").get_data(as_text=True)
    assert 'value="Rice"' in html
    assert 'value="1234.56"' in html
    assert "Edit transaction" in html


def test_edit_saves_changes(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 500, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    response = client.post(f"/transactions/{row_id}/edit", data={
        "type": "expense", "description": "Rice and chicken", "category": "Food",
        "amount": "85.50", "date": "2026-10-02",
    })
    assert response.status_code == 302
    html = client.get("/transactions").get_data(as_text=True)
    assert "Rice and chicken" in html
    assert "₦85.50" in html


def test_edit_with_invalid_data_changes_nothing(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 500, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    response = client.post(f"/transactions/{row_id}/edit", data={
        "type": "expense", "description": "Rice", "category": "Food",
        "amount": "abc", "date": "2026-10-01",
    })
    assert response.status_code == 400
    assert "₦5.00" in client.get("/transactions").get_data(as_text=True)


def test_edit_missing_id_is_404(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/transactions/999/edit").status_code == 404