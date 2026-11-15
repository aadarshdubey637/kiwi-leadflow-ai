from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.database.connection import get_db
from app.schemas.dashboard import ConversionStats, FunnelStage, LeadDistribution, PipelineValue, TrendPoint
from app.schemas.response import ApiResponse
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"], dependencies=[Depends(get_current_admin)])


@router.get("/leads", response_model=ApiResponse[LeadDistribution])
def leads(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.lead_distribution(db))


@router.get("/conversion", response_model=ApiResponse[ConversionStats])
def conversion(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.conversion_stats(db))


@router.get("/funnel", response_model=ApiResponse[list[FunnelStage]])
def funnel(db: Session = Depends(get_db)):
    return ApiResponse(data=analytics_service.funnel(db))


@router.get("/trends", response_model=ApiResponse[list[TrendPoint]])
def trends(
    period: Literal["daily", "weekly", "monthly"] = "daily",
    days: int = Query(30, ge=1, le=366),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=analytics_service.trends(db, period, days))


@router.get("/pipeline", response_model=ApiResponse[PipelineValue])
def pipeline(db: Session = Depends(get_db)):
    """Estimated pipeline value from stated budgets of open enquiries — not revenue."""
    return ApiResponse(data=analytics_service.pipeline_value(db))
