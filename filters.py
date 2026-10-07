def filter_by_date(transactions, date):
    """Return (number, transaction) pairs on exactly this date (YYYY-MM-DD)."""
    results = []
    for i, t in enumerate(transactions, start=1):
        if t.date == date:
            results.append((i, t))
    return results


def filter_by_month(transactions, month):
    """Return (number, transaction) pairs in this month (YYYY-MM)."""
    results = []
    for i, t in enumerate(transactions, start=1):
        if t.date[:7] == month:
            results.append((i, t))
    return results


def filter_by_range(transactions, start, end):
    """Return (number, transaction) pairs from start to end, both included.

    Raises ValueError if start is after end.
    """
    if start > end:
        raise ValueError("Start date must not be after the end date.")
    results = []
    for i, t in enumerate(transactions, start=1):
        if start <= t.date <= end:
            results.append((i, t))
    return results