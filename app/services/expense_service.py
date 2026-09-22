import datetime

from sqlalchemy.orm import Session

from app.models import Expense
from app.schemas import ExpenseCreate


def create_expense(db: Session, expense_data: ExpenseCreate, user_id: int) -> Expense:
    """Create and persist a new expense record for the given user."""
    expense = Expense(
        user_id=user_id,
        amount=expense_data.amount,
        category=expense_data.category,
        note=expense_data.note,
        date=expense_data.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expenses(
    db: Session,
    user_id: int,
    category: str | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> list[Expense]:
    """Retrieve expenses for the given user with optional filtering."""
    query = db.query(Expense).filter(Expense.user_id == user_id)
    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    return query.order_by(Expense.date.desc()).all()
