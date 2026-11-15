from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.database.connection import get_db
from app.schemas.dashboard import CountItem, DashboardStats
from app.schemas.response import ApiResponse
from app.services import analytics_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_admin)])


@router.get("/stats", response_model=ApiResponse[DashboardStats])
def stats(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.dashboard_stats(db))


@router.get("/categories", response_model=ApiResponse[list[CountItem]])
def categories(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.category_distribution(db))


@router.get("/priorities", response_model=ApiResponse[list[CountItem]])
def priorities(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.priority_distribution(db))
