import pytest

import filters
from models import Transaction


def sample():
    return [
        Transaction("income", "Salary", 50000, "2026-10-01"),
        Transaction("expense", "Rice", 5000, "2026-10-07", "Food"),
        Transaction("expense", "Bus fare", 2000, "2026-10-07", "Transport"),
        Transaction("expense", "Shoes", 20000, "2026-09-28", "Shopping"),
        Transaction("expense", "Old rice", 4000, "2025-10-07", "Food"),
    ]


def descriptions(results):
    return [t.description for _, t in results]


def test_exact_date():
    assert descriptions(filters.filter_by_date(sample(), "2026-10-07")) == ["Rice", "Bus fare"]


def test_exact_date_no_match():
    assert filters.filter_by_date(sample(), "2026-01-01") == []


def test_results_keep_original_numbers():
    numbers = [n for n, _ in filters.filter_by_date(sample(), "2026-10-07")]
    assert numbers == [2, 3]


def test_month():
    assert descriptions(filters.filter_by_month(sample(), "2026-10")) == ["Salary", "Rice", "Bus fare"]


def test_month_ignores_same_month_in_other_year():
    assert "Old rice" not in descriptions(filters.filter_by_month(sample(), "2026-10"))


def test_range_includes_both_ends():
    result = filters.filter_by_range(sample(), "2026-10-01", "2026-10-07")
    assert descriptions(result) == ["Salary", "Rice", "Bus fare"]


def test_range_single_day():
    assert descriptions(filters.filter_by_range(sample(), "2026-09-28", "2026-09-28")) == ["Shoes"]


def test_range_start_after_end_raises():
    with pytest.raises(ValueError):
        filters.filter_by_range(sample(), "2026-10-07", "2026-10-01")

def rows():
    return [
        (1, Transaction("income", "Salary", 5000000, "2026-10-01")),
        (2, Transaction("expense", "Rice", 500000, "2026-10-07", "Food")),
        (5, Transaction("expense", "Bus fare", 200000, "2026-09-28", "Transport")),
    ]


def ids(result):
    return [row_id for row_id, _ in result]


def test_filter_rows_no_criteria_returns_everything():
    assert ids(filters.filter_rows(rows())) == [1, 2, 5]


def test_filter_rows_keyword_matches_description_case_insensitively():
    assert ids(filters.filter_rows(rows(), keyword="RICE")) == [2]


def test_filter_rows_keyword_matches_category():
    assert ids(filters.filter_rows(rows(), keyword="transport")) == [5]


def test_filter_rows_by_type():
    assert ids(filters.filter_rows(rows(), kind="expense")) == [2, 5]


def test_filter_rows_date_range_includes_both_ends():
    assert ids(filters.filter_rows(rows(), start="2026-10-01", end="2026-10-07")) == [1, 2]


def test_filter_rows_open_ended_ranges():
    assert ids(filters.filter_rows(rows(), start="2026-10-02")) == [2]
    assert ids(filters.filter_rows(rows(), end="2026-09-30")) == [5]


def test_filter_rows_combines_criteria():
    result = filters.filter_rows(rows(), keyword="o", kind="expense", start="2026-10-01")
    assert ids(result) == [2]


def test_filter_rows_start_after_end_raises():
    with pytest.raises(ValueError):
        filters.filter_rows(rows(), start="2026-10-07", end="2026-10-01")