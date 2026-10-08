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


def first_id(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "test_web.db"))
    row_id = database.get_all_transactions(conn)[0][0]
    conn.close()
    return row_id


def search_client(tmp_path):
    return make_client(tmp_path, [
        Transaction("income", "Salary", 5000000, "2026-10-01"),
        Transaction("expense", "Rice", 500000, "2026-10-07", "Food"),
        Transaction("expense", "Bus fare", 200000, "2026-09-28", "Transport"),
    ])


# ---------- dashboard ----------

def test_dashboard_shows_totals(tmp_path):
    client = make_client(tmp_path, [
        Transaction("income", "Salary", 5000000, "2026-10-01"),
        Transaction("expense", "Rice", 500050, "2026-10-02", "Food"),
    ])
    html = client.get("/").get_data(as_text=True)
    assert "₦50,000.00" in html
    assert "₦5,000.50" in html
    assert "₦44,999.50" in html


def test_dashboard_with_empty_database(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "₦0.00" in response.get_data(as_text=True)


def test_dashboard_shows_monthly_summary_newest_first(tmp_path):
    client = make_client(tmp_path, [
        Transaction("income", "Salary", 5000000, "2026-10-01"),
        Transaction("expense", "Rice", 500050, "2026-10-02", "Food"),
        Transaction("expense", "Shoes", 2000000, "2026-09-28", "Shopping"),
    ])
    html = client.get("/").get_data(as_text=True)
    assert html.index("2026-10") < html.index("2026-09")
    assert "-₦20,000.00" in html


def test_dashboard_monthly_section_empty(tmp_path):
    html = make_client(tmp_path).get("/").get_data(as_text=True)
    assert "No transactions yet." in html


def test_dashboard_shows_only_six_recent_months(tmp_path):
    client = make_client(tmp_path, [
        Transaction("expense", f"Item {m}", 100, f"2026-{m:02d}-01", "Other")
        for m in range(1, 8)
    ])
    html = client.get("/").get_data(as_text=True)
    assert "2026-07" in html and "2026-02" in html
    assert "2026-01" not in html


# ---------- transactions list ----------

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
    html = make_client(tmp_path).get("/transactions").get_data(as_text=True)
    assert "No transactions yet." in html


def test_descriptions_are_escaped(tmp_path):
    client = make_client(tmp_path, [
        Transaction("expense", "<b>bold</b>", 100, "2026-10-01", "Other"),
    ])
    html = client.get("/transactions").get_data(as_text=True)
    assert "<b>bold</b>" not in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html


# ---------- add form ----------

def test_new_transaction_form_loads(tmp_path):
    response = make_client(tmp_path).get("/transactions/new")
    assert response.status_code == 200
    assert "Add transaction" in response.get_data(as_text=True)


def test_valid_expense_is_saved_in_kobo(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "food",
        "amount": "1,234.56", "date": "2026-10-07",
    })
    assert response.status_code == 302
    html = client.get("/transactions").get_data(as_text=True)
    assert "Rice" in html
    assert "Food" in html
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
    response = make_client(tmp_path).post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "Food",
        "amount": "100", "date": "2999-01-01",
    })
    assert response.status_code == 400
    assert "future" in response.get_data(as_text=True)


def test_expense_without_category_is_rejected(tmp_path):
    response = make_client(tmp_path).post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "",
        "amount": "100", "date": "2026-10-07",
    })
    assert response.status_code == 400
    assert "Expenses need a category" in response.get_data(as_text=True)


def test_form_keeps_values_after_an_error(tmp_path):
    response = make_client(tmp_path).post("/transactions/new", data={
        "type": "expense", "description": "Rice and chicken", "category": "Food",
        "amount": "abc", "date": "2026-10-07",
    })
    assert 'value="Rice and chicken"' in response.get_data(as_text=True)


# ---------- delete and edit ----------

def test_delete_removes_the_transaction(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 500, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    response = client.post(f"/transactions/{row_id}/delete")
    assert response.status_code == 302
    assert "No transactions yet." in client.get("/transactions").get_data(as_text=True)


def test_delete_missing_id_is_404(tmp_path):
    assert make_client(tmp_path).post("/transactions/999/delete").status_code == 404


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
    assert make_client(tmp_path).get("/transactions/999/edit").status_code == 404


# ---------- search ----------

def test_search_by_keyword(tmp_path):
    html = search_client(tmp_path).get("/transactions?q=rice").get_data(as_text=True)
    assert "Rice" in html
    assert "Salary" not in html
    assert "Showing 1 of 3" in html


def test_search_by_type(tmp_path):
    html = search_client(tmp_path).get("/transactions?type=income").get_data(as_text=True)
    assert "Salary" in html
    assert "Rice" not in html


def test_search_by_date_range(tmp_path):
    html = search_client(tmp_path).get(
        "/transactions?start=2026-10-01&end=2026-10-31"
    ).get_data(as_text=True)
    assert "Salary" in html and "Rice" in html
    assert "Bus fare" not in html


def test_search_with_no_match(tmp_path):
    html = search_client(tmp_path).get("/transactions?q=zzz").get_data(as_text=True)
    assert "No transactions match your search." in html


def test_search_invalid_date_shows_error_and_does_not_crash(tmp_path):
    response = search_client(tmp_path).get("/transactions?start=abc")
    assert response.status_code == 200
    assert "must be a real date" in response.get_data(as_text=True)


def test_search_start_after_end_shows_error(tmp_path):
    html = search_client(tmp_path).get(
        "/transactions?start=2026-10-07&end=2026-10-01"
    ).get_data(as_text=True)
    assert "cannot be after" in html


def test_filtered_rows_keep_their_real_ids(tmp_path):
    html = search_client(tmp_path).get("/transactions?q=bus").get_data(as_text=True)
    assert "/transactions/3/edit" in html
    assert "/transactions/1/edit" not in html


# ---------- breakdown ----------

def test_breakdown_shows_categories_and_percentages(tmp_path):
    client = make_client(tmp_path, [
        Transaction("income", "Salary", 5000000, "2026-10-01"),
        Transaction("expense", "Rice", 750000, "2026-10-02", "Food"),
        Transaction("expense", "Bus", 250000, "2026-10-03", "Transport"),
    ])
    html = client.get("/breakdown").get_data(as_text=True)
    assert "Food" in html and "Transport" in html
    assert "75.0%" in html and "25.0%" in html
    assert html.index("Food") < html.index("Transport")
    assert "Salary" not in html


def test_breakdown_empty(tmp_path):
    html = make_client(tmp_path).get("/breakdown").get_data(as_text=True)
    assert "No expenses yet." in html


# ---------- layout ----------

def test_stylesheet_is_served(tmp_path):
    response = make_client(tmp_path).get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.content_type


def test_every_page_uses_the_shared_layout(tmp_path):
    client = make_client(tmp_path, [Transaction("expense", "Rice", 500, "2026-10-01", "Food")])
    row_id = first_id(tmp_path)
    for url in ["/", "/transactions", "/transactions/new",
                f"/transactions/{row_id}/edit", "/breakdown"]:
        html = client.get(url).get_data(as_text=True)
        assert "style.css" in html, url
        assert 'class="nav"' in html, url