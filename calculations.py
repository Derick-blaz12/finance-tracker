def total_income(transactions):
    return sum(t.amount for t in transactions if t.type == "income")


def total_expenses(transactions):
    return sum(t.amount for t in transactions if t.type == "expense")


def current_balance(transactions):
    return total_income(transactions) - total_expenses(transactions)


def calculate_average_expense(transactions):
    """Return the average expense, or None if there are no expenses."""
    total = 0
    count = 0

    for t in transactions:
        if t.type != "expense":
            continue  # ignore income
        total += t.amount
        count += 1

    if count == 0:
        return None
    return total / count


def find_largest_expense(transactions):
    """Return (number, transaction) for the biggest expense, or None if there are none."""
    biggest_number = None
    biggest = None

    for i, t in enumerate(transactions, start=1):
        if t.type != "expense":
            continue  # ignore income
        if biggest is None or t.amount > biggest.amount:
            biggest_number = i
            biggest = t

    if biggest is None:
        return None
    return biggest_number, biggest


def calculate_spending_by_category(transactions):
    """Return a list of (category, total) pairs, largest total first."""
    totals = {}

    for t in transactions:
        if t.type != "expense":
            continue  # ignore income
        category = t.category
        if category in totals:
            totals[category] += t.amount
        else:
            totals[category] = t.amount

    return sorted(totals.items(), key=lambda pair: pair[1], reverse=True)

def calculate_monthly_summary(transactions):
    """Return a list of (month, income, expenses, net) tuples, newest month first."""
    months = {}

    for t in transactions:
        month = t.date[:7]
        if month not in months:
            months[month] = {"income": 0, "expenses": 0}
        if t.type == "income":
            months[month]["income"] += t.amount
        else:
            months[month]["expenses"] += t.amount

    summary = []
    for month in sorted(months, reverse=True):
        income = months[month]["income"]
        expenses = months[month]["expenses"]
        summary.append((month, income, expenses, income - expenses))
    return summary

def category_shares(spending):
    """Turn (category, total) pairs into (category, total, percent) tuples.

    percent is each category's share of all spending, rounded to 1 decimal place.
    Returns an empty list if there is no spending.
    """
    grand_total = sum(total for _, total in spending)
    if grand_total == 0:
        return []
    return [
        (category, total, round(total * 100 / grand_total, 1))
        for category, total in spending
    ]