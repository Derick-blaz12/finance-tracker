from datetime import date, datetime


def get_amount():
    """Keep asking until the user enters a valid positive number."""
    while True:
        try:
            amount = float(input("Amount: "))
            if amount <= 0:
                print("Amount must be greater than 0.")
                continue
            return amount
        except ValueError:
            print("Please enter a valid number.")


def get_description():
    """Keep asking until the user enters a non-empty description."""
    while True:
        description = input("Description: ").strip()
        if description:
            return description
        print("Description cannot be empty.")


def get_date(prompt="Date (YYYY-MM-DD, press Enter for today): "):
    """Return a date string (YYYY-MM-DD). Enter = today. Keeps asking until valid."""
    while True:
        entry = input(prompt).strip()
        if not entry:
            return date.today().isoformat()
        try:
            parsed = datetime.strptime(entry, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD, e.g. 2026-09-28.")
            continue
        if parsed > date.today():
            print("Date cannot be in the future.")
            continue
        return parsed.isoformat()

def get_month():
    """Return a month string (YYYY-MM). Keeps asking until valid."""
    while True:
        entry = input("Month (YYYY-MM): ").strip()
        try:
            parsed = datetime.strptime(entry, "%Y-%m")
        except ValueError:
            print("Invalid month. Use YYYY-MM, e.g. 2026-10.")
            continue
        return f"{parsed.year:04d}-{parsed.month:02d}"


def get_category():
    """Show a numbered list of categories and return the one the user picks."""
    categories = ["Food", "Transport", "Shopping", "Bills", "Health", "Entertainment", "Other"]
    print("Categories:")
    for i, name in enumerate(categories, start=1):
        print(f"  {i}. {name}")
    while True:
        choice = input("Pick a category (number or type your own): ").strip()
        if choice.isdecimal() and 1 <= int(choice) <= len(categories):
            return categories[int(choice) - 1]
        if choice and not choice.isdecimal():
            return choice.title()
        print("Invalid choice. Try again.")


def choose(options, title=None):
    """Show a numbered menu and return the number the user picks (1-based)."""
    if title:
        print(f"\n{title}")
    for i, name in enumerate(options, start=1):
        print(f"{i}. {name}")

    while True:
        choice = input(f"Choose (1-{len(options)}): ").strip()
        if choice.isdecimal() and 1 <= int(choice) <= len(options):
            return int(choice)
        print(f"Invalid choice. Enter a number from 1 to {len(options)}.")


def get_transaction_number(count):
    """Return a valid 1-based number up to count, or None if the user cancels with 0."""
    while True:
        try:
            number = int(input(f"Transaction number (1-{count}, 0 to cancel): "))
        except ValueError:
            print("Please enter a valid number.")
            continue
        if number == 0:
            return None
        if 1 <= number <= count:
            return number
        print(f"Pick a number between 1 and {count}.")