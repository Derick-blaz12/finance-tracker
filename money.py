import re
from decimal import Decimal

# Plain digits, optionally followed by a dot and 1 or 2 decimal digits
_AMOUNT_PATTERN = re.compile(r"[0-9]+(\.[0-9]{1,2})?")


def parse_naira(text):
    """Convert text like '5,000.50' to an integer number of kobo (500050).

    Accepts an optional ₦ sign and thousands commas. Raises ValueError for
    anything else, including more than 2 decimal places.
    """
    cleaned = text.strip().replace("₦", "").replace(",", "")
    if not _AMOUNT_PATTERN.fullmatch(cleaned):
        raise ValueError(f"Not a valid naira amount: {text!r}")
    return int(Decimal(cleaned) * 100)


def format_naira(kobo):
    """Convert an integer number of kobo to text like '₦5,000.50'."""
    sign = "-" if kobo < 0 else ""
    naira, remainder = divmod(abs(kobo), 100)
    return f"{sign}₦{naira:,}.{remainder:02d}"