"""FundFlow assistant: grounded chat over saved audits + portfolio.

Never triggers a fresh Anakin call. Uses saved audit evidence as grounding context
for Gemini (Groq fallback). Voice-friendly, concise answers.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional, Dict, Any, List

from config import settings
from services import fund_audit_service as audit_svc
from services import store_service

logger = logging.getLogger("fundflow.assistant")

SYSTEM = (
    "You are FundFlow's assistant. Answer in simple English (or Hinglish if the user uses it). "
    "Be concise and suitable for voice playback. Ground every answer in the provided audit "
    "evidence and portfolio context. If evidence is missing, say so. Never give personalised "
    "buy/sell advice as certainty. Do not fabricate numbers."
)


async def _gemini(prompt: str) -> Optional[str]:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        resp = model.generate_content(prompt, generation_config={"temperature": 0.3})
        return (resp.text or "").strip() or None
    except Exception as e:
        logger.warning(f"assistant gemini failed: {e}")
        return None


async def _groq(prompt: str) -> Optional[str]:
    if not settings.GROQ_API_KEY:
        return None
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}], temperature=0.3, max_tokens=400)
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as e:
        logger.warning(f"assistant groq failed: {e}")
        return None


async def _openai(prompt: str) -> Optional[str]:
    """Fallback for chat when Groq is unavailable."""
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}], temperature=0.3, max_tokens=500)
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as e:
        logger.warning(f"assistant openai failed: {e}")
        return None


def _audit_context(audit: Dict[str, Any]) -> str:
    lines = [f"Fund: {audit.get('fund_name')} | Trust score: {audit.get('trust_score')} | Verdict: {audit.get('verdict')}"]
    for c in audit.get("checks", []):
        lines.append(f"- {c['name']}: {c['status']} ({c['score']}). {c['summary']}")
        for f in c.get("findings", [])[:2]:
            lines.append(f"   * {f}")
    return "\n".join(lines)


async def chat(user_id: str, message: str, audit_id: Optional[str] = None,
               conversation_id: Optional[str] = None) -> Dict[str, Any]:
    conversation_id = conversation_id or "conv_" + uuid.uuid4().hex[:10]
    audit = audit_svc.get_audit(audit_id) if audit_id else None
    evidence_refs: List[Dict[str, Any]] = []
    context_parts = []
    if audit:
        context_parts.append("AUDIT EVIDENCE:\n" + _audit_context(audit))
        evidence_refs = [{"id": e.get("id"), "title": e.get("title"), "url": e.get("url")}
                         for e in audit.get("evidence", [])[:5]]
    try:
        portfolio = await store_service.get_portfolio(user_id)
        if portfolio:
            holdings = portfolio.get("holdings", [])[:8]
            context_parts.append("PORTFOLIO:\n" + ", ".join(h.get("fund_name", "") for h in holdings))
    except Exception:
        pass

    prompt = f"{SYSTEM}\n\n{chr(10).join(context_parts)}\n\nUser: {message}\nAssistant:"
    # Groq is primary for chat (fast); OpenAI is the fallback. Gemini last (often rate-limited).
    answer = await _groq(prompt) or await _openai(prompt) or await _gemini(prompt)
    if not answer:
        answer = ("I can explain saved audit results and your portfolio, but the language model is "
                  "currently unavailable. Please try again shortly.")
    return {
        "answer": answer,
        "evidence": evidence_refs,
        "suggested_actions": _suggestions(audit),
        "conversation_id": conversation_id,
        "used_cached_audit": bool(audit),
    }


def _suggestions(audit: Optional[Dict[str, Any]]) -> List[str]:
    if audit:
        return ["Why did this fund receive a warning?", "What did the manager say?",
                "What actually changed in the holdings?", "Read this verdict aloud."]
    return ["How is my portfolio performing?", "Which holding has the highest risk?",
            "Audit my largest holding."]


def build_audit_narration(audit: Dict[str, Any]) -> str:
    """<=140 word voice script summarising the audit."""
    warnings = [c for c in audit.get("checks", []) if c.get("status") in ("warning", "fail")]
    positives = [c for c in audit.get("checks", []) if c.get("status") == "pass"]
    parts = [
        f"Here is the FundFlow audit for {audit.get('fund_name')}.",
        f"The trust score is {audit.get('trust_score')} out of 100, giving a verdict of {audit.get('verdict')}.",
    ]
    for w in warnings[:2]:
        parts.append(f"{w['name']}: {w['summary']}")
    if positives:
        parts.append(f"On the positive side, {positives[0]['name']} looks consistent.")
    parts.append("This is an AI-assisted consistency audit, not investment advice. Please verify the source documents.")
    script = " ".join(parts)
    words = script.split()
    if len(words) > 140:
        script = " ".join(words[:140])
    return script
