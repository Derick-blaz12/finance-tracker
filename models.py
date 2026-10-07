from dataclasses import dataclass
from datetime import datetime
from typing import Optional

INCOME = "income"
EXPENSE = "expense"


@dataclass
class Transaction:
    type: str
    description: str
    amount: float
    date: str
    category: Optional[str] = None

    def __post_init__(self):
        if self.type not in (INCOME, EXPENSE):
            raise ValueError(f"Type must be '{INCOME}' or '{EXPENSE}', not {self.type!r}.")

        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("Description cannot be empty.")
        self.description = self.description.strip()

        if (isinstance(self.amount, bool)
                or not isinstance(self.amount, (int, float))
                or not self.amount > 0):
            raise ValueError("Amount must be a number greater than 0.")

        try:
            parsed = datetime.strptime(self.date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError(f"Date must be YYYY-MM-DD, not {self.date!r}.")
        self.date = parsed.isoformat()

        if self.type == EXPENSE:
            if not isinstance(self.category, str) or not self.category.strip():
                raise ValueError("Expenses need a category.")
            self.category = self.category.strip()
        elif self.category is not None:
            raise ValueError("Income transactions have no category.")

    def to_dict(self):
        """Return a plain dictionary in the same shape your JSON file already uses."""
        d = {
            "type": self.type,
            "description": self.description,
            "amount": self.amount,
            "date": self.date,
        }
        if self.category is not None:
            d["category"] = self.category
        return d

    @classmethod
    def from_dict(cls, d):
        """Build a Transaction from a dictionary, e.g. one loaded from JSON."""
        try:
            return cls(
                type=d["type"],
                description=d["description"],
                amount=d["amount"],
                date=d["date"],
                category=d.get("category"),
            )
        except KeyError as e:
            raise ValueError(f"Transaction is missing the field {e}.")