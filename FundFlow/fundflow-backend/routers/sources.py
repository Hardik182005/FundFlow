"""Fund source registry endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services import fund_source_service as sources
from models.audit_schemas import FundSource

router = APIRouter()


@router.get("/funds")
async def list_funds():
    return {"funds": sources.list_funds()}


@router.get("/funds/{scheme_code}")
async def get_fund(scheme_code: str):
    f = sources.get_fund(scheme_code)
    if not f:
        raise HTTPException(status_code=404, detail="Fund not found in source registry.")
    return f


@router.put("/funds/{scheme_code}")
async def put_fund(scheme_code: str, body: FundSource):
    return sources.upsert_fund(scheme_code, body.model_dump())


class ValidateRequest(BaseModel):
    url: str
    user_id: Optional[str] = "developer"


@router.post("/validate")
async def validate(req: ValidateRequest):
    return await sources.validate_source(req.url, req.user_id or "developer")
