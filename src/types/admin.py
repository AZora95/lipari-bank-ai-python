from datetime import datetime

from pydantic import BaseModel


class ModelCostBreakdown(BaseModel):
    model: str
    cost_eur: float
    tokens: int
    messages: int


class CostReportResponse(BaseModel):
    since: datetime
    until: datetime
    total_cost_eur: float
    total_tokens: int
    total_messages: int
    by_model: list[ModelCostBreakdown]
