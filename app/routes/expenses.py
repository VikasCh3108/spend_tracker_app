import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ExpenseCreate, ExpenseResponse
from app.services.expense_service import create_expense, get_expenses

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Create a new expense record."""
    created = create_expense(db, expense, current_user.id)
    return ExpenseResponse.model_validate(created)


@router.get("/", response_model=list[ExpenseResponse])
def list_expenses(
    category: str | None = Query(None, description="Filter by category"),
    start_date: datetime.date | None = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="Filter end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseResponse]:
    """List expenses, optionally filtered by category and/or date range."""
    expenses = get_expenses(
        db, current_user.id, category=category, start_date=start_date, end_date=end_date
    )
    return [ExpenseResponse.model_validate(e) for e in expenses]
