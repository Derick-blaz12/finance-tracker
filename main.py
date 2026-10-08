import getpass

import calculations
import database
import tracker
import users
from money import format_naira

MAX_LOGIN_ATTEMPTS = 3


def log_in(connection):
    """Ask for email and password. Return the user's id, or None after 3 failures."""
    for _ in range(MAX_LOGIN_ATTEMPTS):
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        user_id = users.authenticate(connection, email, password)
        if user_id is not None:
            return user_id
        print("Incorrect email or password.")
    return None


def show_menu():
    print("\n=== Finance Tracker ===")
    print("1. Add income")
    print("2. Add an expense")
    print("3. View all transactions")
    print("4. Calculate total income")
    print("5. Calculate total expenses")
    print("6. Calculate current balance")
    print("7. Delete a transaction")
    print("8. Edit a transaction")
    print("9. Search transactions")
    print("10. Statistics")
    print("11. Exit")


def main():
    tracker.connection = database.connect()
    database.create_table(tracker.connection)
    users.create_users_table(tracker.connection)

    try:
        print("Log in with the account you created in the web app.")
        tracker.user_id = log_in(tracker.connection)
        if tracker.user_id is None:
            print("Too many failed attempts.")
            return

        while True:
            show_menu()
            choice = input("Choose an option (1-11): ").strip()

            if choice == "1":
                tracker.add_transaction("income")
            elif choice == "2":
                tracker.add_transaction("expense")
            elif choice == "3":
                tracker.view_transactions()
            elif choice == "4":
                transactions = tracker.load_transactions()
                print(f"Total income: {format_naira(calculations.total_income(transactions))}")
            elif choice == "5":
                transactions = tracker.load_transactions()
                print(f"Total expenses: {format_naira(calculations.total_expenses(transactions))}")
            elif choice == "6":
                transactions = tracker.load_transactions()
                print(f"Current balance: {format_naira(calculations.current_balance(transactions))}")
            elif choice == "7":
                tracker.delete_transaction()
            elif choice == "8":
                tracker.edit_transaction()
            elif choice == "9":
                tracker.search_transactions()
            elif choice == "10":
                tracker.show_statistics()
            elif choice == "11":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Pick a number from 1 to 11.")
    finally:
        tracker.connection.close()


if __name__ == "__main__":
    main()