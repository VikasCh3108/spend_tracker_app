import datetime

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    """Schema for creating a new expense. FastAPI auto-validates against this."""

    amount: float = Field(gt=0, description="Amount must be a positive number")
    category: str = Field(min_length=1, max_length=50, description="Category name")
    note: str | None = Field(default=None, max_length=500, description="Optional note")
    date: datetime.date = Field(description="Date of the expense (YYYY-MM-DD)")


class ExpenseResponse(BaseModel):
    """Schema for returning an expense. Converts ORM objects via from_attributes."""

    id: int
    amount: float
    category: str
    note: str | None
    date: datetime.date
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class MoMChange(BaseModel):
    """Month-over-month spend change."""

    current_month: str
    previous_month: str
    current_spend: float
    previous_spend: float
    change_percent: float | None
    note: str | None = None


class SummaryResponse(BaseModel):
    """Schema for the summary endpoint."""

    total_spend: float
    spend_by_category: dict[str, float]
    mom_change: MoMChange


class InsightResponse(BaseModel):
    """Schema for a single category insight (bonus)."""

    category: str
    current_month_spend: float
    previous_month_spend: float
    increase_percent: float
    flagged: bool


class Token(BaseModel):
    """Schema for JWT auth response (bonus)."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT payload (bonus)."""

    username: str | None = None


class UserCreate(BaseModel):
    """Schema for user registration (bonus)."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
