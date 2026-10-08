import sqlite3
from datetime import date, datetime

from flask import Flask, abort, g, redirect, render_template, request, url_for

import calculations
import database
from input_helpers import CATEGORIES
from models import Transaction
from money import format_naira, parse_naira

def build_transaction_from_form(form):
    """Return (Transaction, []) if the form is valid, or (None, [error messages])."""
    errors = []
    kind = form.get("type", "")
    description = form.get("description", "")
    category = form.get("category", "").strip().title()
    date_text = form.get("date", "").strip() or date.today().isoformat()

    amount = None
    try:
        amount = parse_naira(form.get("amount", ""))
    except ValueError:
        errors.append("Amount must be a number like 5000 or 5000.50 (at most 2 decimal places).")
    else:
        if amount <= 0:
            errors.append("Amount must be greater than 0.")

    parsed = None
    try:
        parsed = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        errors.append("Date must be a real date in YYYY-MM-DD format.")
    else:
        if parsed > date.today():
            errors.append("Date cannot be in the future.")

    if errors:
        return None, errors

    try:
        t = Transaction(
            kind, description, amount, parsed.isoformat(),
            category if kind == "expense" else None,
        )
    except ValueError as e:
        return None, [str(e)]
    return t, []

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

    @app.route("/transactions/new", methods=["GET", "POST"])
    def new_transaction():
        if request.method == "POST":
            t, errors = build_transaction_from_form(request.form)
            if t is not None:
                database.add_transaction(get_db(), t)
                return redirect(url_for("transactions_page"))
            return render_template(
                "transaction_form.html",
                errors=errors, form=request.form, categories=CATEGORIES,
            ), 400
        return render_template(
            "transaction_form.html",
            errors=[], form={"type": "expense", "date": date.today().isoformat()},
            categories=CATEGORIES,
        )

    @app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
    def delete_transaction(transaction_id):
        if not database.delete_transaction(get_db(), transaction_id):
            abort(404)
        return redirect(url_for("transactions_page"))

    @app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
    def edit_transaction(transaction_id):
        existing = database.get_transaction(get_db(), transaction_id)
        if existing is None:
            abort(404)

        if request.method == "POST":
            t, errors = build_transaction_from_form(request.form)
            if t is not None:
                database.replace_transaction(get_db(), transaction_id, t)
                return redirect(url_for("transactions_page"))
            return render_template(
                "transaction_form.html", errors=errors, form=request.form,
                categories=CATEGORIES, editing=True,
            ), 400

        form = {
            "type": existing.type,
            "description": existing.description,
            "category": existing.category or "",
            "amount": f"{existing.amount // 100}.{existing.amount % 100:02d}",
            "date": existing.date,
        }
        return render_template(
            "transaction_form.html", errors=[], form=form,
            categories=CATEGORIES, editing=True,
        )

    return app