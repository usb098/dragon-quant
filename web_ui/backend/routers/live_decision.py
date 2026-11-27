"""Explicit, read-only intraday quote observations for selected prep candidates."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from dragon_quant.intelligence.live_monitor import monitor_quotes
from ..deps import live_quote_providers

router = APIRouter(tags=["live-decision"])


class LiveMonitorRequest(BaseModel):
    codes: list[str] = Field(min_length=1, max_length=30)


@router.post("/api/live-decision/monitor")
def live_decision_monitor(payload: LiveMonitorRequest, providers=Depends(live_quote_providers)):
    """Fetch current quotes only after an explicit user refresh action."""
    try:
        return monitor_quotes(payload.codes, providers)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(exc)) from exc
