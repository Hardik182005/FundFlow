"""FundFlow assistant (chatbot) endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from services import assistant_service

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str = "demo-user"
    message: str
    audit_id: Optional[str] = None
    conversation_id: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest):
    return await assistant_service.chat(req.user_id, req.message, req.audit_id, req.conversation_id)


@router.get("/context/{user_id}")
async def context(user_id: str):
    from services import store_service
    portfolio = await store_service.get_portfolio(user_id)
    return {"user_id": user_id, "has_portfolio": bool(portfolio)}


@router.get("/suggestions/{user_id}")
async def suggestions(user_id: str):
    return {"suggestions": assistant_service._suggestions(None)}
