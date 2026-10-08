import calculations

from models import Transaction

def tx(kind, description, amount, category=None):
    """Build a Transaction for a test."""
    return Transaction(kind, description, amount, "2026-10-04", category)

# ---------- totals and balance ----------

def test_total_income():
    data = [tx("income", "Salary", 50000), tx("income", "Freelance", 10000),
            tx("expense", "Rice", 5000, "Food")]
    assert calculations.total_income(data) == 60000


def test_total_expenses():
    data = [tx("income", "Salary", 50000), tx("expense", "Rice", 5000, "Food"),
            tx("expense", "Bus fare", 2000, "Transport")]
    assert calculations.total_expenses(data) == 7000


def test_totals_when_empty():
    assert calculations.total_income([]) == 0
    assert calculations.total_expenses([]) == 0


def test_current_balance():
    data = [tx("income", "Salary", 50000), tx("expense", "Rice", 5000, "Food")]
    assert calculations.current_balance(data) == 45000


# ---------- average expense ----------

def test_calculate_average_expense():
    data = [tx("expense", "A", 10000, "Other"), tx("expense", "B", 20000, "Other"),
            tx("expense", "C", 30000, "Other"), tx("income", "Salary", 50000)]
    assert calculations.calculate_average_expense(data) == 20000


def test_calculate_average_expense_with_no_expenses():
    assert calculations.calculate_average_expense([tx("income", "Salary", 50000)]) is None


# ---------- largest expense ----------

def test_find_largest_expense():
    data = [tx("income", "Salary", 200000), tx("expense", "Rice", 5000, "Food"),
            tx("expense", "Rent", 120000, "Bills")]
    number, t = calculations.find_largest_expense(data)
    assert number == 3
    assert t.description == "Rent"
    assert t.amount == 120000


def test_find_largest_expense_tie_keeps_first():
    data = [tx("expense", "First", 1000, "Other"), tx("expense", "Second", 1000, "Other")]
    number, t = calculations.find_largest_expense(data)
    assert number == 1
    assert t.description == "First"


def test_find_largest_expense_with_no_expenses():
    assert calculations.find_largest_expense([tx("income", "Salary", 50000)]) is None


# ---------- spending by category ----------

def test_calculate_spending_by_category():
    data = [tx("expense", "Rice", 5000, "Food"), tx("expense", "Chicken", 8500, "Food"),
            tx("expense", "Bus fare", 2000, "Transport"), tx("income", "Salary", 200000)]
    assert calculations.calculate_spending_by_category(data) == [
        ("Food", 13500),
        ("Transport", 2000),
    ]


def test_calculate_spending_by_category_sorted_largest_first():
    data = [tx("expense", "Bus fare", 8000, "Transport"), tx("expense", "Shoes", 45000, "Shopping"),
            tx("expense", "Rice", 25000, "Food")]
    result = calculations.calculate_spending_by_category(data)
    assert [category for category, amount in result] == ["Shopping", "Food", "Transport"]


def test_calculate_spending_by_category_with_no_expenses():
    assert calculations.calculate_spending_by_category([tx("income", "Salary", 50000)]) == []

# ---------- monthly summary ----------

def test_monthly_summary_groups_by_month_newest_first():
    data = [
        Transaction("income", "Salary", 50000, "2026-10-01"),
        Transaction("expense", "Rice", 5000, "2026-10-07", "Food"),
        Transaction("expense", "Shoes", 20000, "2026-09-28", "Shopping"),
        Transaction("income", "Gift", 10000, "2026-09-15"),
    ]
    assert calculations.calculate_monthly_summary(data) == [
        ("2026-10", 50000, 5000, 45000),
        ("2026-09", 10000, 20000, -10000),
    ]


def test_monthly_summary_separates_years():
    data = [
        Transaction("expense", "A", 100, "2026-10-01", "Other"),
        Transaction("expense", "B", 200, "2025-10-01", "Other"),
    ]
    result = calculations.calculate_monthly_summary(data)
    assert [row[0] for row in result] == ["2026-10", "2025-10"]


def test_monthly_summary_month_with_only_expenses():
    data = [Transaction("expense", "Rice", 5000, "2026-10-07", "Food")]
    assert calculations.calculate_monthly_summary(data) == [("2026-10", 0, 5000, -5000)]


def test_monthly_summary_when_empty():
    assert calculations.calculate_monthly_summary([]) == []

def test_category_shares():
    spending = [("Food", 7500), ("Transport", 2500)]
    assert calculations.category_shares(spending) == [
        ("Food", 7500, 75.0),
        ("Transport", 2500, 25.0),
    ]


def test_category_shares_rounds_to_one_decimal():
    result = calculations.category_shares([("A", 1), ("B", 2)])
    assert [row[2] for row in result] == [33.3, 66.7]


def test_category_shares_empty():
    assert calculations.category_shares([]) == []