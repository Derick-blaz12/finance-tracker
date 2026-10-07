from datetime import date
from helpers import fake_inputs

import input_helpers


# ---------- choose ----------

def test_choose_returns_the_number(monkeypatch):
    fake_inputs(monkeypatch, ["2"])
    assert input_helpers.choose(["A", "B", "C"]) == 2


def test_choose_asks_again_on_bad_input(monkeypatch, capsys):
    fake_inputs(monkeypatch, ["abc", "0", "5", "", "3"])
    assert input_helpers.choose(["A", "B", "C"]) == 3
    assert capsys.readouterr().out.count("Invalid choice") == 4


def test_choose_prints_numbered_options(monkeypatch, capsys):
    fake_inputs(monkeypatch, ["1"])
    input_helpers.choose(["Income", "Expense"], title="Pick one")
    out = capsys.readouterr().out
    assert "Pick one" in out
    assert "1. Income" in out
    assert "2. Expense" in out


# ---------- get_category ----------

def test_get_category_by_number(monkeypatch):
    fake_inputs(monkeypatch, ["2"])
    assert input_helpers.get_category() == "Transport"


def test_get_category_custom_is_title_cased(monkeypatch):
    fake_inputs(monkeypatch, ["grooming"])
    assert input_helpers.get_category() == "Grooming"


def test_get_category_asks_again_on_bad_input(monkeypatch, capsys):
    fake_inputs(monkeypatch, ["99", "", "1"])
    assert input_helpers.get_category() == "Food"
    assert capsys.readouterr().out.count("Invalid choice") == 2


# ---------- get_amount ----------

def test_get_amount_rejects_bad_input_then_accepts(monkeypatch):
    fake_inputs(monkeypatch, ["abc", "-50", "0", "1500.5"])
    assert input_helpers.get_amount() == 1500.5


# ---------- get_description ----------

def test_get_description_rejects_empty_and_spaces(monkeypatch, capsys):
    fake_inputs(monkeypatch, ["", "   ", "  Rice and chicken  "])
    assert input_helpers.get_description() == "Rice and chicken"
    assert capsys.readouterr().out.count("cannot be empty") == 2


# ---------- get_date ----------

def test_get_date_enter_means_today(monkeypatch):
    fake_inputs(monkeypatch, [""])
    assert input_helpers.get_date() == date.today().isoformat()


def test_get_date_pads_to_standard_format(monkeypatch):
    fake_inputs(monkeypatch, ["2026-9-5"])
    assert input_helpers.get_date() == "2026-09-05"


def test_get_date_rejects_invalid_and_future(monkeypatch, capsys):
    fake_inputs(monkeypatch, ["abc", "2026-02-30", "28-09-2026", "2999-01-01", "2026-09-28"])
    assert input_helpers.get_date() == "2026-09-28"
    out = capsys.readouterr().out
    assert out.count("Invalid date") == 3
    assert out.count("future") == 1


# ---------- get_transaction_number ----------

def test_get_transaction_number_valid(monkeypatch):
    fake_inputs(monkeypatch, ["abc", "2.5", "99", "-1", "2"])
    assert input_helpers.get_transaction_number(3) == 2


def test_get_transaction_number_zero_cancels(monkeypatch):
    fake_inputs(monkeypatch, ["0"])
    assert input_helpers.get_transaction_number(3) is None

# ---------- get_month ----------

def test_get_month_valid(monkeypatch):
    fake_inputs(monkeypatch, ["2026-10"])
    assert input_helpers.get_month() == "2026-10"


def test_get_month_pads_to_standard_format(monkeypatch):
    fake_inputs(monkeypatch, ["2026-9"])
    assert input_helpers.get_month() == "2026-09"


def test_get_month_rejects_bad_input(monkeypatch, capsys):
    fake_inputs(monkeypatch, ["abc", "2026-13", "10-2026", "", "2026-10"])
    assert input_helpers.get_month() == "2026-10"
    assert capsys.readouterr().out.count("Invalid month") == 4


# ---------- get_date with a custom prompt ----------

def test_get_date_uses_custom_prompt(monkeypatch):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt="": prompts.append(prompt) or "2026-09-28")
    assert input_helpers.get_date("From: ") == "2026-09-28"
    assert prompts == ["From: "]