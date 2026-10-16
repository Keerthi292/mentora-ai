from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Counts for each page and the learning goals with their latest progress."""
    return dashboard_service.get_dashboard(db, user_id)
