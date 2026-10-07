import storage
import json

from models import Transaction

def use_temp_file(monkeypatch, tmp_path):
    """Point storage at a throwaway file instead of the real one."""
    path = tmp_path / "test_data.json"
    monkeypatch.setattr(storage, "DATA_FILE", str(path))
    return path


def test_save_then_load_round_trip(monkeypatch, tmp_path):
    use_temp_file(monkeypatch, tmp_path)
    data = [
        Transaction("income", "Salary", 50000, "2026-10-04"),
        Transaction("expense", "Rice", 5000, "2026-10-04", "Food"),
    ]
    storage.save_transactions(data)
    assert storage.load_transactions() == data


def test_save_overwrites_previous_contents(monkeypatch, tmp_path):
    use_temp_file(monkeypatch, tmp_path)
    storage.save_transactions([Transaction("income", "Old", 1, "2026-10-04")])
    storage.save_transactions([])
    assert storage.load_transactions() == []


def test_valid_file_creates_no_backup(monkeypatch, tmp_path):
    use_temp_file(monkeypatch, tmp_path)
    storage.save_transactions([Transaction("income", "Salary", 50000, "2026-10-04")])
    storage.load_transactions()
    assert not (tmp_path / "test_data.json.bak").exists()


def test_load_when_file_missing_returns_empty_list(monkeypatch, tmp_path):
    use_temp_file(monkeypatch, tmp_path)
    assert storage.load_transactions() == []


def test_load_damaged_file_returns_empty_list_and_warns(monkeypatch, tmp_path, capsys):
    path = use_temp_file(monkeypatch, tmp_path)
    path.write_text("[{ this is not valid json", encoding="utf-8")
    assert storage.load_transactions() == []
    assert "damaged" in capsys.readouterr().out


def test_load_skips_invalid_records_and_warns(monkeypatch, tmp_path, capsys):
    path = use_temp_file(monkeypatch, tmp_path)
    good = {"type": "income", "description": "Salary", "amount": 50000, "date": "2026-10-04"}
    bad_amount = {"type": "expense", "description": "Rice", "amount": -5,
                  "date": "2026-10-04", "category": "Food"}
    missing_field = {"type": "income", "description": "Oops"}
    path.write_text(json.dumps([good, bad_amount, "not a record", missing_field]), encoding="utf-8")

    assert storage.load_transactions() == [Transaction.from_dict(good)]
    assert "skipped 3" in capsys.readouterr().out


def test_load_wrong_format_returns_empty_list(monkeypatch, tmp_path, capsys):
    path = use_temp_file(monkeypatch, tmp_path)
    path.write_text('{"not": "a list"}', encoding="utf-8")
    assert storage.load_transactions() == []
    assert "wrong format" in capsys.readouterr().out


def test_skipped_records_trigger_a_backup(monkeypatch, tmp_path):
    path = use_temp_file(monkeypatch, tmp_path)
    raw = json.dumps([{"type": "income", "description": "Bad"}])
    path.write_text(raw, encoding="utf-8")

    storage.load_transactions()
    backup = tmp_path / "test_data.json.bak"
    assert backup.read_text(encoding="utf-8") == raw
