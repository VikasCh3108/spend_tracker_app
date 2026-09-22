import datetime
from calendar import monthrange

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Expense
from app.schemas import InsightResponse, MoMChange, SummaryResponse

INSIGHT_THRESHOLD_PERCENT = 20.0


def _get_month_boundaries(
    ref_date: datetime.date,
) -> tuple[datetime.date, datetime.date, datetime.date, datetime.date]:
    """Return (prev_month_start, prev_month_end, current_month_start, current_month_end).

    Handles year boundaries correctly (e.g., Jan → Dec of previous year).
    """
    current_month_start = ref_date.replace(day=1)
    current_month_end = ref_date.replace(
        day=monthrange(ref_date.year, ref_date.month)[1]
    )

    if ref_date.month == 1:
        prev_month_start = ref_date.replace(year=ref_date.year - 1, month=12, day=1)
    else:
        prev_month_start = ref_date.replace(month=ref_date.month - 1, day=1)
    prev_month_end = current_month_start - datetime.timedelta(days=1)

    return prev_month_start, prev_month_end, current_month_start, current_month_end


def get_total_spend(db: Session, user_id: int) -> float:
    """Return the total sum of all expenses for the given user."""
    result = db.query(func.sum(Expense.amount)).filter(Expense.user_id == user_id).scalar()
    return float(result) if result is not None else 0.0


def get_spend_by_category(db: Session, user_id: int) -> dict[str, float]:
    """Return a mapping of category to total spend for the given user."""
    rows = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.user_id == user_id)
        .group_by(Expense.category)
        .all()
    )
    return {category: float(total) for category, total in rows}


def get_mom_change(db: Session, user_id: int, ref_date: datetime.date | None = None) -> MoMChange:
    """Calculate month-over-month spend change.

    Compares the current calendar month's total spend against the previous
    calendar month.  If *ref_date* is None, today's date is used.
    """
    if ref_date is None:
        ref_date = datetime.date.today()

    prev_month_start, prev_month_end, current_month_start, current_month_end = (
        _get_month_boundaries(ref_date)
    )

    current_spend = (
        db.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= current_month_start,
            Expense.date <= current_month_end,
        )
        .scalar()
    )
    previous_spend = (
        db.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= prev_month_start,
            Expense.date <= prev_month_end,
        )
        .scalar()
    )

    current_spend = float(current_spend) if current_spend else 0.0
    previous_spend = float(previous_spend) if previous_spend else 0.0

    if previous_spend > 0:
        change_percent = round(
            ((current_spend - previous_spend) / previous_spend) * 100, 2
        )
        note = None
    elif current_spend > 0:
        change_percent = None
        note = "No spend in previous month; new spending detected this month"
    else:
        change_percent = None
        note = "No spend in either month"

    return MoMChange(
        current_month=current_month_start.strftime("%Y-%m"),
        previous_month=prev_month_start.strftime("%Y-%m"),
        current_spend=current_spend,
        previous_spend=previous_spend,
        change_percent=change_percent,
        note=note,
    )


def get_summary(
    db: Session, user_id: int, ref_date: datetime.date | None = None
) -> SummaryResponse:
    """Return the full summary: total, by category, and MoM change."""
    return SummaryResponse(
        total_spend=get_total_spend(db, user_id),
        spend_by_category=get_spend_by_category(db, user_id),
        mom_change=get_mom_change(db, user_id, ref_date=ref_date),
    )


def get_category_insights(
    db: Session, user_id: int, ref_date: datetime.date | None = None
) -> list[InsightResponse]:
    """Flag categories where spend increased more than 20% vs previous month.

    Only categories with spend in the previous month are considered — a
    category with no prior spend cannot have a meaningful percentage increase.
    """
    if ref_date is None:
        ref_date = datetime.date.today()

    prev_month_start, prev_month_end, current_month_start, current_month_end = (
        _get_month_boundaries(ref_date)
    )

    # Query per-category spend for both months in a single pass
    prev_rows = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= prev_month_start,
            Expense.date <= prev_month_end,
        )
        .group_by(Expense.category)
        .all()
    )
    curr_rows = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= current_month_start,
            Expense.date <= current_month_end,
        )
        .group_by(Expense.category)
        .all()
    )

    prev_spend = {cat: float(total) for cat, total in prev_rows}
    curr_spend = {cat: float(total) for cat, total in curr_rows}

    insights: list[InsightResponse] = []
    for category, prev_amount in prev_spend.items():
        curr_amount = curr_spend.get(category, 0.0)
        increase_percent = round(((curr_amount - prev_amount) / prev_amount) * 100, 2)
        flagged = increase_percent > INSIGHT_THRESHOLD_PERCENT
        insights.append(
            InsightResponse(
                category=category,
                current_month_spend=curr_amount,
                previous_month_spend=prev_amount,
                increase_percent=increase_percent,
                flagged=flagged,
            )
        )

    # Sort: flagged first, then by largest increase
    insights.sort(key=lambda x: (not x.flagged, -x.increase_percent))
    return insights
