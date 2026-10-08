import calculations
import database
import filters
from input_helpers import (
    choose,
    get_amount,
    get_category,
    get_date,
    get_description,
    get_month,
    get_transaction_number,
)
from models import Transaction
from money import format_naira

connection = None  # set by main.py (and by the tests)
user_id = None     # the logged-in user's id, set by main.py (and by the tests)


def load_rows():
    """Return [(id, Transaction), ...] for the logged-in user."""
    return database.get_all_transactions(connection, user_id)


def load_transactions():
    """Return just the Transaction objects."""
    return [t for _, t in load_rows()]


def format_transaction(number, t):
    """Return one display line for a transaction."""
    line = f"{number}. {t.date} | [{t.type}] {t.description}"
    if t.category:
        line += f" | {t.category}"
    line += f" | {format_naira(t.amount)}"
    return line


def view_transactions():
    transactions = load_transactions()
    if not transactions:
        print("No transactions yet.")
        return
    print("\n--- All Transactions ---")
    for i, t in enumerate(transactions, start=1):
        print(format_transaction(i, t))


def delete_transaction():
    rows = load_rows()
    if not rows:
        print("No transactions to delete.")
        return

    view_transactions()
    number = get_transaction_number(len(rows))
    if number is None:
        print("Cancelled.")
        return

    row_id, t = rows[number - 1]  # screen number -> database id
    confirm = input(f"Delete '{t.description}' ({format_naira(t.amount)})? (y/n): ").strip().lower()
    if confirm == "y":
        database.delete_transaction(connection, user_id, row_id)
        print("Transaction deleted.")
    else:
        print("Cancelled.")


def edit_transaction():
    rows = load_rows()
    if not rows:
        print("No transactions to edit.")
        return

    view_transactions()
    number = get_transaction_number(len(rows))
    if number is None:
        print("Cancelled.")
        return

    row_id, t = rows[number - 1]  # screen number -> database id

    # Show what is being edited
    parts = [t.description]
    if t.category:
        parts.append(t.category)
    parts.append(format_naira(t.amount))
    parts.append(t.date)
    print("\nEditing: " + " | ".join(parts))

    # Income has no category, so only expenses get that option
    fields = ["Description", "Amount", "Date"]
    if t.type == "expense":
        fields.insert(1, "Category")

    choice = choose(fields + ["Cancel"], title="What do you want to edit?")
    if choice == len(fields) + 1:
        print("Cancelled.")
        return

    field = fields[choice - 1]
    if field == "Description":
        database.update_transaction(connection, user_id, row_id, "description", get_description())
    elif field == "Category":
        database.update_transaction(connection, user_id, row_id, "category", get_category())
    elif field == "Amount":
        database.update_transaction(connection, user_id, row_id, "amount", get_amount())
    elif field == "Date":
        database.update_transaction(connection, user_id, row_id, "date", get_date())

    print(f"{field} updated!")


def show_results(results):
    """Print search results (a list of (number, transaction) pairs)."""
    print("\n--- Search Results ---")
    for number, t in results:
        print(format_transaction(number, t))
    print(f"\n{len(results)} found.")


def search_by_keyword():
    keyword = input("Search: ").strip().lower()
    if not keyword:
        print("Search term cannot be empty.")
        return

    results = []
    for i, t in enumerate(load_transactions(), start=1):
        in_description = keyword in t.description.lower()
        in_category = keyword in (t.category or "").lower()
        if in_description or in_category:
            results.append((i, t))

    if not results:
        print(f"No transactions found for '{keyword}'.")
        return
    show_results(results)


def search_by_type():
    choice = choose(["Income", "Expense"], title="Search by type")
    kind = "income" if choice == 1 else "expense"

    results = []
    for i, t in enumerate(load_transactions(), start=1):
        if t.type == kind:
            results.append((i, t))

    if not results:
        print(f"No {kind} transactions found.")
        return
    show_results(results)


def search_by_exact_date():
    date = get_date("Date (YYYY-MM-DD, press Enter for today): ")
    results = filters.filter_by_date(load_transactions(), date)
    if not results:
        print(f"No transactions found on {date}.")
        return
    show_results(results)


def search_by_month():
    month = get_month()
    results = filters.filter_by_month(load_transactions(), month)
    if not results:
        print(f"No transactions found in {month}.")
        return
    show_results(results)


def search_by_range():
    while True:
        start = get_date("From (YYYY-MM-DD, press Enter for today): ")
        end = get_date("To (YYYY-MM-DD, press Enter for today): ")
        if start <= end:
            break
        print("The start date cannot be after the end date. Try again.")

    results = filters.filter_by_range(load_transactions(), start, end)
    if not results:
        print(f"No transactions found from {start} to {end}.")
        return
    show_results(results)


def search_by_date():
    choice = choose(
        ["Exact date", "Month", "Date range", "Cancel"],
        title="--- Search by date ---",
    )
    if choice == 1:
        search_by_exact_date()
    elif choice == 2:
        search_by_month()
    elif choice == 3:
        search_by_range()
    else:
        print("Cancelled.")


def search_transactions():
    if not load_transactions():
        print("No transactions to search.")
        return

    choice = choose(
        ["Search by keyword", "Search by type", "Search by date", "Cancel"],
        title="--- Search Transactions ---",
    )
    if choice == 1:
        search_by_keyword()
    elif choice == 2:
        search_by_type()
    elif choice == 3:
        search_by_date()
    else:
        print("Cancelled.")


def largest_expense():
    """Print the largest expense."""
    result = calculations.find_largest_expense(load_transactions())
    if result is None:
        print("No expenses yet.")
        return

    number, t = result
    print("\nLargest expense:")
    print(format_transaction(number, t))


def average_expense():
    """Print the average expense."""
    average = calculations.calculate_average_expense(load_transactions())
    if average is None:
        print("No expenses yet.")
        return
    print(f"\nAverage expense: {format_naira(round(average))}")


def spending_by_category():
    """Print spending grouped by category."""
    ranked = calculations.calculate_spending_by_category(load_transactions())
    if not ranked:
        print("No expenses yet.")
        return

    print("\n--- Spending by Category ---")
    for category, amount in ranked:
        print(f"{category}: {format_naira(amount)}")


def monthly_summary():
    """Print income, expenses and net for each month."""
    summary = calculations.calculate_monthly_summary(load_transactions())
    if not summary:
        print("No transactions yet.")
        return

    print("\n--- Monthly Summary ---")
    for month, income, expenses, net in summary:
        print(
            f"{month} | Income: {format_naira(income)} | "
            f"Expenses: {format_naira(expenses)} | Net: {format_naira(net)}"
        )


def show_statistics():
    transactions = load_transactions()
    if not transactions:
        print("No transactions yet.")
        return

    choice = choose(
        [
            "Total income",
            "Total expenses",
            "Largest expense",
            "Average expense",
            "Spending by category",
            "Monthly summary",
            "Cancel",
        ],
        title="--- Statistics ---",
    )
    if choice == 1:
        print(f"Total income: {format_naira(calculations.total_income(transactions))}")
    elif choice == 2:
        print(f"Total expenses: {format_naira(calculations.total_expenses(transactions))}")
    elif choice == 3:
        largest_expense()
    elif choice == 4:
        average_expense()
    elif choice == 5:
        spending_by_category()
    elif choice == 6:
        monthly_summary()
    else:
        print("Cancelled.")


def add_transaction(kind):
    description = get_description()
    category = get_category() if kind == "expense" else None
    amount = get_amount()
    transaction_date = get_date()
    t = Transaction(kind, description, amount, transaction_date, category)
    database.add_transaction(connection, user_id, t)
    print(f"{kind.capitalize()} added!")