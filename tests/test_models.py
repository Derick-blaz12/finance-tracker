import pytest

from models import Transaction


def make_expense(**overrides):
    fields = {"type": "expense", "description": "Rice", "amount": 5000,
              "date": "2026-10-04", "category": "Food"}
    fields.update(overrides)
    return Transaction(**fields)


def test_create_expense():
    t = make_expense()
    assert t.description == "Rice"
    assert t.amount == 5000
    assert t.category == "Food"


def test_create_income_has_no_category():
    t = Transaction("income", "Salary", 50000, "2026-10-04")
    assert t.category is None


def test_expense_requires_category():
    with pytest.raises(ValueError):
        make_expense(category=None)
    with pytest.raises(ValueError):
        make_expense(category="   ")


def test_income_rejects_category():
    with pytest.raises(ValueError):
        Transaction("income", "Salary", 50000, "2026-10-04", "Food")


def test_rejects_unknown_type():
    with pytest.raises(ValueError):
        make_expense(type="expence")


def test_rejects_empty_description():
    for bad in ["", "   ", None]:
        with pytest.raises(ValueError):
            make_expense(description=bad)


def test_description_is_stripped():
    assert make_expense(description="  Rice  ").description == "Rice"


def test_rejects_non_positive_amount():
    for bad in [0, -5]:
        with pytest.raises(ValueError):
            make_expense(amount=bad)


def test_rejects_non_number_amount():
    for bad in ["100", None, True]:
        with pytest.raises(ValueError):
            make_expense(amount=bad)


def test_rejects_invalid_date():
    for bad in ["abc", "2026-02-30", "28-09-2026", None]:
        with pytest.raises(ValueError):
            make_expense(date=bad)


def test_date_is_normalized():
    assert make_expense(date="2026-9-5").date == "2026-09-05"


def test_to_dict_expense():
    assert make_expense().to_dict() == {
        "type": "expense", "description": "Rice", "amount": 5000,
        "date": "2026-10-04", "category": "Food",
    }


def test_to_dict_income_has_no_category_key():
    t = Transaction("income", "Salary", 50000, "2026-10-04")
    assert "category" not in t.to_dict()


def test_from_dict_round_trip():
    expense = {"type": "expense", "description": "Rice", "amount": 5000,
               "date": "2026-10-04", "category": "Food"}
    income = {"type": "income", "description": "Salary", "amount": 50000,
              "date": "2026-10-04"}
    assert Transaction.from_dict(expense).to_dict() == expense
    assert Transaction.from_dict(income).to_dict() == income


def test_from_dict_missing_key_raises():
    with pytest.raises(ValueError):
        Transaction.from_dict({"type": "income", "description": "Salary"})


def test_misspelled_field_name_is_an_error():
    with pytest.raises(TypeError):
        Transaction(type="expense", descripton="Rice", amount=5000,
                    date="2026-10-04", category="Food")

def test_rejects_float_amount():
    for bad in [5000.5, 5000.0]:
        with pytest.raises(ValueError):
            make_expense(amount=bad)


def test_accepts_integer_kobo():
    assert make_expense(amount=500050).amount == 500050