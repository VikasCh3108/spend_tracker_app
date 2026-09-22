import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import SummaryResponse
from app.services.summary_service import get_summary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/", response_model=SummaryResponse)
def summary(
    ref_date: datetime.date | None = Query(
        None, description="Reference date for MoM calculation (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummaryResponse:
    """Return total spend, spend by category, and month-over-month change."""
    return get_summary(db, current_user.id, ref_date=ref_date)
