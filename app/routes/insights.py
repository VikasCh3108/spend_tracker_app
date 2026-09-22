import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import InsightResponse
from app.services.summary_service import get_category_insights

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/", response_model=list[InsightResponse])
def insights(
    ref_date: datetime.date | None = Query(
        None, description="Reference date for month comparison (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InsightResponse]:
    """Flag categories where spend increased more than 20% vs previous month."""
    return get_category_insights(db, current_user.id, ref_date=ref_date)
