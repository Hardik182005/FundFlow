"""Anakin usage + Wire discovery developer endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from services import anakin_budget_service as budget
from services import wire_registry_service as wire_reg

router = APIRouter()


@router.get("/usage")
async def usage():
    return budget.usage_report()


class DiscoverRequest(BaseModel):
    logical_names: Optional[List[str]] = None


@router.post("/discover-wire-actions")
async def discover(req: DiscoverRequest = DiscoverRequest()):
    try:
        return await wire_reg.discover_wire_actions(req.logical_names)
    except Exception as e:
        raise HTTPException(status_code=502, detail="Wire discovery could not be completed.")


@router.get("/wire-actions")
async def wire_actions():
    return {"actions": wire_reg.list_actions()}
