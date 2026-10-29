from fastapi import APIRouter

from budget_tracker.core.database import DbSession
from budget_tracker.core.types import Month
from budget_tracker.summary import service
from budget_tracker.summary.schemas import MonthlySummary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/{month}")
def get_monthly_summary(month: Month, db: DbSession) -> MonthlySummary:
    return service.get_monthly_summary(db, month)
