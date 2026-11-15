from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    total_enquiries: int
    new_enquiries: int
    high_priority_enquiries: int
    in_progress_enquiries: int
    converted_enquiries: int
    closed_enquiries: int
    needs_manual_review: int
    ai_failed: int


class CountItem(BaseModel):
    label: str
    count: int
    percentage: float


class LeadDistribution(BaseModel):
    hot: int
    warm: int
    cold: int
    unscored: int
    average_score: float | None
    score_buckets: list[CountItem]  # 0-19, 20-39, ...


class ConversionStats(BaseModel):
    total_enquiries: int
    converted: int
    closed: int
    open: int
    conversion_rate: float  # converted / total, percent
    by_temperature: list[dict]


class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage_of_total: float


class TrendPoint(BaseModel):
    period: str
    count: int


class PipelineCurrency(BaseModel):
    currency: str
    enquiries: int
    estimated_pipeline_value: float


class PipelineValue(BaseModel):
    note: str
    by_currency: list[PipelineCurrency]
    open_enquiries_without_budget: int


class ProviderUsage(BaseModel):
    provider: str
    model_name: str
    requests: int
    successful: int
    failed: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    average_response_time: float


class AIUsageStats(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    retry_count: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    average_response_time: float
    cost_note: str
    by_provider: list[ProviderUsage]


class PerformanceStats(BaseModel):
    ai_success_rate: float
    average_latency_seconds: float
    p95_latency_seconds: float
    workflows_completed: int
    workflows_failed: int
    workflow_success_rate: float
    average_workflow_seconds: float
    latency_by_provider: list[dict]


class WorkflowLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enquiry_id: int
    workflow_step: str
    execution_status: Literal["started", "success", "failed", "skipped"]
    message: str | None
    execution_time: float | None
    created_at: datetime
