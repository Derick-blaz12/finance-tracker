import pytest
from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app


def test_database_file_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_FILE", "/data/prod.db")
    app = create_app(secret_key="k", csrf=False)
    assert app.config["DB_FILE"] == "/data/prod.db"


def test_explicit_db_file_wins_over_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_FILE", "/data/prod.db")
    app = create_app(str(tmp_path / "x.db"), secret_key="k")
    assert app.config["DB_FILE"] == str(tmp_path / "x.db")


def test_production_without_secret_key_refuses_to_start(monkeypatch, tmp_path):
    monkeypatch.setenv("PRODUCTION", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app(str(tmp_path / "x.db"))


def test_proxy_headers_are_trusted_only_when_enabled(monkeypatch, tmp_path):
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    assert not isinstance(create_app(str(tmp_path / "a.db"), secret_key="k").wsgi_app, ProxyFix)
    monkeypatch.setenv("TRUSTED_PROXIES", "1")
    assert isinstance(create_app(str(tmp_path / "b.db"), secret_key="k").wsgi_app, ProxyFix)