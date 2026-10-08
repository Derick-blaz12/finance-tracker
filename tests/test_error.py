from app import create_app


def make_app(tmp_path, **kwargs):
    return create_app(str(tmp_path / "e.db"), secret_key="test-secret", **kwargs)


def test_404_uses_the_friendly_page(tmp_path):
    response = make_app(tmp_path, csrf=False).test_client().get("/no-such-page")
    assert response.status_code == 404
    assert "Page not found" in response.get_data(as_text=True)


def test_csrf_failure_uses_the_friendly_page(tmp_path):
    response = make_app(tmp_path).test_client().post("/login", data={"email": "a@b.co"})
    assert response.status_code == 400
    assert "Request not accepted" in response.get_data(as_text=True)


def test_secure_cookie_flag_follows_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("PRODUCTION", "1")
    assert make_app(tmp_path).config["SESSION_COOKIE_SECURE"] is True
    monkeypatch.delenv("PRODUCTION")
    assert make_app(tmp_path).config["SESSION_COOKIE_SECURE"] is False