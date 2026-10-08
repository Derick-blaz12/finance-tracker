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

def filter_rows(rows, keyword="", kind="", start="", end=""):
    """Filter (id, Transaction) pairs. Empty criteria are ignored.

    keyword: matches description or category, case-insensitive
    kind: "income" or "expense"
    start, end: YYYY-MM-DD, both included

    Raises ValueError if start is after end.
    """
    if start and end and start > end:
        raise ValueError("Start date must not be after the end date.")

    keyword = keyword.strip().lower()
    results = []
    for row_id, t in rows:
        if keyword and keyword not in t.description.lower() \
                and keyword not in (t.category or "").lower():
            continue
        if kind and t.type != kind:
            continue
        if start and t.date < start:
            continue
        if end and t.date > end:
            continue
        results.append((row_id, t))
    return results