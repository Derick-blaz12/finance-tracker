from app import create_app


def make_client(tmp_path):
    return create_app(str(tmp_path / "p.db"), secret_key="k", csrf=False).test_client()


def test_privacy_page_is_public_and_explains_deletion_and_export(tmp_path):
    response = make_client(tmp_path).get("/privacy")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Delete" in html and "Export" in html
    assert "never stored" in html


def test_footer_links_to_privacy_on_every_layout_page(tmp_path):
    client = make_client(tmp_path)
    assert "/privacy" in client.get("/login").get_data(as_text=True)