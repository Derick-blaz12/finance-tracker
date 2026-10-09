import csv
import io

HEADER = ["date", "type", "description", "category", "amount_naira"]


def _safe_cell(text):
    """Stop spreadsheets treating text as a formula."""
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def kobo_to_decimal(kobo):
    sign = "-" if kobo < 0 else ""
    naira, rest = divmod(abs(kobo), 100)
    return f"{sign}{naira}.{rest:02d}"


def transactions_to_csv(rows):
    """Turn [(id, Transaction), ...] into CSV text, newest first."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADER)
    for _, t in sorted(rows, key=lambda row: (row[1].date, row[0]), reverse=True):
        writer.writerow([
            t.date,
            t.type,
            _safe_cell(t.description),
            _safe_cell(t.category or ""),
            kobo_to_decimal(t.amount),
        ])
    return output.getvalue()