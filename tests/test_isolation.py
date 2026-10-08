import sqlite3

import database
from app import create_app


def make_two_users(tmp_path):
    db_file = str(tmp_path / "iso.db")
    app = create_app(db_file, secret_key="test-secret")
    ada, grace = app.test_client(), app.test_client()   # separate cookie jars
    ada.post("/register", data={"email": "ada@example.com", "password": "correct horse"})
    grace.post("/register", data={"email": "grace@example.com", "password": "another horse"})
    return db_file, ada, grace


def add_expense(client, description="Secret rice", amount="123.45", category="Food"):
    client.post("/transactions/new", data={
        "type": "expense", "description": description, "category": category,
        "amount": amount, "date": "2026-10-07",
    })


def owner_of(db_file, transaction_id):
    conn = sqlite3.connect(db_file)
    owner = conn.execute(
        "SELECT user_id FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()[0]
    conn.close()
    return owner


def test_new_transaction_is_owned_by_its_creator(tmp_path):
    db_file, ada, grace = make_two_users(tmp_path)
    add_expense(ada, "Ada's item")
    add_expense(grace, "Grace's item")
    assert owner_of(db_file, 1) == 1
    assert owner_of(db_file, 2) == 2


def test_user_b_does_not_see_user_a_transactions(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    html = grace.get("/transactions").get_data(as_text=True)
    assert "Secret rice" not in html
    assert "No transactions yet." in html


def test_each_user_sees_only_their_own(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada, "Ada's item")
    add_expense(grace, "Grace's item")
    assert "Grace's item" not in ada.get("/transactions").get_data(as_text=True)
    assert "Ada's item" not in grace.get("/transactions").get_data(as_text=True)


def test_dashboard_totals_are_per_user(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    html = grace.get("/").get_data(as_text=True)
    assert "₦0.00" in html
    assert "123.45" not in html


def test_breakdown_is_per_user(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    html = grace.get("/breakdown").get_data(as_text=True)
    assert "No expenses yet." in html
    assert "Food" not in html


def test_search_is_per_user(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    html = grace.get("/transactions?q=rice").get_data(as_text=True)
    assert "Secret rice" not in html


def test_user_b_cannot_open_the_edit_page_of_user_a(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    assert grace.get("/transactions/1/edit").status_code == 404


def test_user_b_cannot_edit_user_a_transaction(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    response = grace.post("/transactions/1/edit", data={
        "type": "expense", "description": "Hijacked", "category": "Food",
        "amount": "1", "date": "2026-10-07",
    })
    assert response.status_code == 404
    html = ada.get("/transactions").get_data(as_text=True)
    assert "Secret rice" in html and "₦123.45" in html
    assert "Hijacked" not in html


def test_user_b_cannot_delete_user_a_transaction(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    assert grace.post("/transactions/1/delete").status_code == 404
    assert "Secret rice" in ada.get("/transactions").get_data(as_text=True)


def test_foreign_and_missing_ids_look_identical(tmp_path):
    _, ada, grace = make_two_users(tmp_path)
    add_expense(ada)
    foreign = grace.get("/transactions/1/edit")
    missing = grace.get("/transactions/999/edit")
    assert foreign.status_code == missing.status_code == 404