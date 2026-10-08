import sqlite3

from flask import Flask, g, render_template

import calculations
import database
from money import format_naira


def create_app(db_file=None):
    app = Flask(__name__)
    app.config["DB_FILE"] = db_file or database.DB_FILE
    app.jinja_env.filters["naira"] = format_naira

    def get_db():
        """One connection per request, created on first use."""
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_FILE"])
            database.create_table(g.db)
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.route("/")
    def dashboard():
        rows = database.get_all_transactions(get_db())
        transactions = [t for _, t in rows]
        return render_template(
            "dashboard.html",
            income=calculations.total_income(transactions),
            expenses=calculations.total_expenses(transactions),
            balance=calculations.current_balance(transactions),
        )

    @app.route("/transactions")
    def transactions_page():
        rows = database.get_all_transactions(get_db())
        # newest date first; ties broken by id so the order is stable
        rows.sort(key=lambda row: (row[1].date, row[0]), reverse=True)
        return render_template("transactions.html", rows=rows)

    return app