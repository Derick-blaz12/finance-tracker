import re

from app import create_app


def make_app(tmp_path):
    return create_app(str(tmp_path / "csrf.db"), secret_key="test-secret")  # CSRF on


def token_from(html):
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def register(client, email="ada@example.com"):
    token = token_from(client.get("/register").get_data(as_text=True))
    return client.post("/register", data={
        "email": email, "password": "correct horse", "csrf_token": token,
    })


def add_expense(client):
    token = token_from(client.get("/transactions/new").get_data(as_text=True))
    return client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "Food",
        "amount": "100", "date": "2026-10-07", "csrf_token": token,
    })


def test_post_without_token_is_rejected(tmp_path):
    client = make_app(tmp_path).test_client()
    response = client.post("/register", data={
        "email": "ada@example.com", "password": "correct horse",
    })
    assert response.status_code == 400


def test_register_with_token_works(tmp_path):
    client = make_app(tmp_path).test_client()
    assert register(client).status_code == 302


def test_wrong_token_is_rejected(tmp_path):
    client = make_app(tmp_path).test_client()
    client.get("/register")
    response = client.post("/register", data={
        "email": "ada@example.com", "password": "correct horse",
        "csrf_token": "not-a-real-token",
    })
    assert response.status_code == 400


def test_logged_in_create_without_token_is_rejected(tmp_path):
    client = make_app(tmp_path).test_client()
    register(client)
    response = client.post("/transactions/new", data={
        "type": "expense", "description": "Rice", "category": "Food",
        "amount": "100", "date": "2026-10-07",
    })
    assert response.status_code == 400
    assert "No transactions yet." in client.get("/transactions").get_data(as_text=True)


def test_delete_without_token_does_nothing(tmp_path):
    client = make_app(tmp_path).test_client()
    register(client)
    add_expense(client)
    assert client.post("/transactions/1/delete").status_code == 400
    assert "Rice" in client.get("/transactions").get_data(as_text=True)


def test_logout_without_token_keeps_you_logged_in(tmp_path):
    client = make_app(tmp_path).test_client()
    register(client)
    assert client.post("/logout").status_code == 400
    assert client.get("/").status_code == 200


def test_every_post_form_contains_a_token(tmp_path):
    app = make_app(tmp_path)
    anonymous = app.test_client()
    for url in ["/login", "/register"]:
        html = anonymous.get(url).get_data(as_text=True)
        assert html.count('method="post"') >= 1, url
        assert html.count('method="post"') == html.count('name="csrf_token"'), url

    user = app.test_client()
    register(user)
    add_expense(user)
    for url in ["/", "/transactions", "/transactions/new",
                "/transactions/1/edit", "/breakdown"]:
        html = user.get(url).get_data(as_text=True)
        assert html.count('method="post"') >= 1, url
        assert html.count('method="post"') == html.count('name="csrf_token"'), url