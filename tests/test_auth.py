import pytest

from app import create_app


def make_app(tmp_path):
    return create_app(str(tmp_path / "auth.db"), secret_key="test-secret")


def register(client, email="ada@example.com", password="correct horse"):
    return client.post("/register", data={"email": email, "password": password})


def login(client, email="ada@example.com", password="correct horse"):
    return client.post("/login", data={"email": email, "password": password})


def test_register_and_login_pages_load(tmp_path):
    client = make_app(tmp_path).test_client()
    assert client.get("/register").status_code == 200
    assert client.get("/login").status_code == 200


def test_register_creates_account_and_logs_in(tmp_path):
    client = make_app(tmp_path).test_client()
    assert register(client).status_code == 302
    html = client.get("/").get_data(as_text=True)
    assert "ada@example.com" in html
    assert "Log out" in html


def test_register_rejects_duplicate_email(tmp_path):
    app = make_app(tmp_path)
    register(app.test_client())
    response = register(app.test_client(), email="ADA@example.com")
    assert response.status_code == 400
    assert "already exists" in response.get_data(as_text=True)


def test_register_rejects_short_password(tmp_path):
    response = register(make_app(tmp_path).test_client(), password="short")
    assert response.status_code == 400
    assert "at least 8" in response.get_data(as_text=True)


def test_register_rejects_invalid_email(tmp_path):
    response = register(make_app(tmp_path).test_client(), email="not-an-email")
    assert response.status_code == 400
    assert "valid email" in response.get_data(as_text=True)


def test_failed_register_never_echoes_the_password(tmp_path):
    response = register(make_app(tmp_path).test_client(), email="bad", password="pw-secret-1")
    assert "pw-secret-1" not in response.get_data(as_text=True)


def test_login_success(tmp_path):
    app = make_app(tmp_path)
    register(app.test_client())
    client = app.test_client()
    assert login(client).status_code == 302
    assert "ada@example.com" in client.get("/").get_data(as_text=True)


def test_login_email_is_case_insensitive(tmp_path):
    app = make_app(tmp_path)
    register(app.test_client())
    client = app.test_client()
    assert login(client, email="  ADA@Example.com ").status_code == 302


def test_login_wrong_password(tmp_path):
    app = make_app(tmp_path)
    register(app.test_client())
    response = login(app.test_client(), password="wrong horse")
    assert response.status_code == 400
    assert "Incorrect email or password." in response.get_data(as_text=True)


def test_login_unknown_email_gives_the_same_message(tmp_path):
    response = login(make_app(tmp_path).test_client(), email="nobody@example.com")
    assert response.status_code == 400
    assert "Incorrect email or password." in response.get_data(as_text=True)


def test_logout_clears_the_session(tmp_path):
    client = make_app(tmp_path).test_client()
    register(client)
    assert client.post("/logout").status_code == 302
    html = client.get("/").get_data(as_text=True)
    assert "ada@example.com" not in html
    assert "Log in" in html


def test_logout_by_get_is_not_allowed(tmp_path):
    client = make_app(tmp_path).test_client()
    register(client)
    assert client.get("/logout").status_code == 405


def test_session_cookie_is_httponly_and_samesite(tmp_path):
    response = register(make_app(tmp_path).test_client())
    cookie = " ".join(response.headers.getlist("Set-Cookie"))
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_secret_key_is_read_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "from-the-environment")
    app = create_app(str(tmp_path / "auth.db"))
    assert app.config["SECRET_KEY"] == "from-the-environment"


def test_missing_secret_key_falls_back_to_a_random_one(tmp_path, monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    first = create_app(str(tmp_path / "a.db")).config["SECRET_KEY"]
    second = create_app(str(tmp_path / "b.db")).config["SECRET_KEY"]
    assert first != second
    assert len(first) >= 32