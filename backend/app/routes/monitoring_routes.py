from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.database.connection import get_db
from app.schemas.dashboard import AIUsageStats, PerformanceStats
from app.schemas.response import ApiResponse
from app.services import analytics_service

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"], dependencies=[Depends(get_current_admin)])


@router.get("/ai-usage", response_model=ApiResponse[AIUsageStats])
def ai_usage(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.ai_usage_stats(db))


@router.get("/performance", response_model=ApiResponse[PerformanceStats])
def performance(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.performance_stats(db))
