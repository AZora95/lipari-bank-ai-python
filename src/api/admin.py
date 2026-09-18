from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repos import ChatRepository
from src.db.session import get_db
from src.types.admin import CostReportResponse, ModelCostBreakdown

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/cost-report", response_model=CostReportResponse)
async def cost_report(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> CostReportResponse:
    since = datetime.now(UTC) - timedelta(days=days)
    repo = ChatRepository(db)
    rows = await repo.cost_report(since)

    by_model = [
        ModelCostBreakdown(
            model=model or "unknown",
            cost_eur=cost or 0.0,
            tokens=tokens or 0,
            messages=messages,
        )
        for model, cost, tokens, messages in rows
    ]

    return CostReportResponse(
        since=since,
        until=datetime.now(UTC),
        total_cost_eur=sum(b.cost_eur for b in by_model),
        total_tokens=sum(b.tokens for b in by_model),
        total_messages=sum(b.messages for b in by_model),
        by_model=by_model,
    )
