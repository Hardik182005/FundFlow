"""Gemini (Groq fallback) extraction layer.

Anakin returns clean Markdown; this layer turns Markdown into strict JSON. The LLM
is NEVER used to compute numeric differences (that happens in Python). All numbers
extracted here are values *quoted from the document*, not inferred.

Hardening:
- temperature 0, JSON-only prompts with an exact schema.
- on parse failure: strip code fences -> json repair -> one retry with the error
  -> insufficient_data. Never more than one automatic retry.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional, Dict, Any, List

from config import settings

logger = logging.getLogger("fundflow.extract")

_DISCLAIMER_NOTE = (
    "Extract only what is explicitly present. Do NOT infer, estimate, or invent any "
    "number. If a value is absent, use null. Return VALID JSON ONLY, no prose, no code fences."
)


# ----------------------- LLM plumbing -----------------------

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


async def _openai(prompt: str) -> Optional[str]:
    """OpenAI is the primary engine for complex structured extraction."""
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as e:
        logger.warning(f"OpenAI extraction failed: {e}")
        return None


async def _gemini(prompt: str) -> Optional[str]:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
            request_options={"timeout": 8},  # fail fast so fallbacks stay within request limits
        )
        return (resp.text or "").strip() or None
    except Exception as e:
        logger.warning(f"Gemini extraction failed: {e}")
        return None


async def _groq(prompt: str) -> Optional[str]:
    if not settings.GROQ_API_KEY:
        return None
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=1500,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as e:
        logger.warning(f"Groq extraction failed: {e}")
        return None


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _try_parse(text: str) -> Optional[Any]:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # JSON repair: grab outermost object/array
    for o, c in (("{", "}"), ("[", "]")):
        s, e = cleaned.find(o), cleaned.rfind(c)
        if s != -1 and e > s:
            try:
                return json.loads(cleaned[s:e + 1])
            except Exception:
                continue
    return None


async def _extract(prompt: str) -> Optional[Any]:
    """OpenAI (primary, complex tasks) -> Groq (fast fallback) -> Gemini (last).

    One repair-retry on the primary engine; never more than that automatically.
    """
    # primary: OpenAI
    raw = await _openai(prompt)
    parsed = _try_parse(raw) if raw else None
    if parsed is not None:
        return parsed
    if raw:
        retry = await _openai(prompt + "\n\nYour previous reply was not valid JSON. Return ONLY valid JSON now.")
        parsed = _try_parse(retry) if retry else None
        if parsed is not None:
            return parsed
    # fallback: Groq
    raw2 = await _groq(prompt)
    parsed = _try_parse(raw2) if raw2 else None
    if parsed is not None:
        return parsed
    # last resort: Gemini (fast-timeout)
    raw3 = await _gemini(prompt)
    return _try_parse(raw3) if raw3 else None


def _truncate(markdown: str, limit: int = 14000) -> str:
    return markdown[:limit] if markdown else ""


# ----------------------- Extraction functions -----------------------

async def extract_document_metadata(markdown: str, source_url: str = "") -> Dict[str, Any]:
    prompt = f"""You are a financial document parser. {_DISCLAIMER_NOTE}
Schema: {{"document_type": string|null, "fund_name": string|null, "reporting_period": string|null, "published_date": string|null, "title": string|null, "is_mutual_fund_document": boolean, "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown, 6000)}"""
    return await _extract(prompt) or {"is_mutual_fund_document": False, "confidence": 0.0}


async def extract_manager_claims(markdown: str, source_url: str = "") -> List[Dict[str, Any]]:
    prompt = f"""Extract the fund manager's forward-looking PORTFOLIO-ACTION statements (e.g. "we remain underweight financials", "we are adding consumer discretionary", "trimmed IT"). {_DISCLAIMER_NOTE}
Ignore generic market commentary that does not promise a portfolio action.
Return a JSON ARRAY. Each item: {{"asset_or_sector": string, "direction": one of ["increase","decrease","overweight","underweight","maintain","avoid","unknown"], "quoted_text": string (exact short quote), "normalized_claim": string, "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    out = await _extract(prompt)
    return out if isinstance(out, list) else []


async def extract_sector_allocation(markdown: str, source_url: str = "") -> List[Dict[str, Any]]:
    prompt = f"""Extract the sector allocation table (sector name + percentage weight). {_DISCLAIMER_NOTE}
Return a JSON ARRAY of {{"name": string, "weight": number}} where weight is a percentage (0-100). Only include rows explicitly present.
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    out = await _extract(prompt)
    return out if isinstance(out, list) else []


async def extract_holdings(markdown: str, source_url: str = "") -> List[Dict[str, Any]]:
    prompt = f"""Extract the equity holdings table (security/company name + portfolio weight %). {_DISCLAIMER_NOTE}
Return a JSON ARRAY of {{"name": string, "weight": number, "market_cap_segment": one of ["large","mid","small",null]}}.
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    out = await _extract(prompt)
    return out if isinstance(out, list) else []


async def extract_scheme_mandate(markdown: str, source_url: str = "") -> Dict[str, Any]:
    prompt = f"""Extract the scheme mandate / investment objective constraints. {_DISCLAIMER_NOTE}
Schema: {{"category": string|null, "min_largecap_pct": number|null, "min_midcap_pct": number|null, "min_smallcap_pct": number|null, "min_equity_pct": number|null, "max_debt_pct": number|null, "max_international_pct": number|null, "sector_or_theme_constraint": string|null, "mandate_text": string|null, "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    return await _extract(prompt) or {"confidence": 0.0}


async def extract_manager_information(markdown: str, source_url: str = "") -> Dict[str, Any]:
    prompt = f"""Extract fund manager information. {_DISCLAIMER_NOTE}
Schema: {{"current_manager": string|null, "manager_start_date": string|null, "previous_manager": string|null, "manager_change_date": string|null, "advertised_return_periods": [string], "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    return await _extract(prompt) or {"confidence": 0.0}


async def extract_skin_in_game(markdown: str, source_url: str = "") -> Dict[str, Any]:
    prompt = f"""Extract fund manager investment ('skin in the game') disclosure if explicitly present. {_DISCLAIMER_NOTE}
Schema: {{"manager_name": string|null, "amount_invested": string|null, "disclosure_period": string|null, "scheme_name": string|null, "disclosed": boolean, "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    return await _extract(prompt) or {"disclosed": False, "confidence": 0.0}


async def extract_turnover_ratio(markdown: str, source_url: str = "") -> Dict[str, Any]:
    prompt = f"""Extract the published portfolio turnover ratio if present. {_DISCLAIMER_NOTE}
Schema: {{"turnover_ratio_pct": number|null, "reporting_period": string|null, "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown, 8000)}"""
    return await _extract(prompt) or {"turnover_ratio_pct": None, "confidence": 0.0}


async def extract_nfo_mandate(markdown: str, source_url: str = "") -> Dict[str, Any]:
    prompt = f"""Extract the NFO scheme proposition. {_DISCLAIMER_NOTE}
Schema: {{"category": string|null, "benchmark": string|null, "market_cap_mandate": string|null, "sector_or_theme": string|null, "international_exposure": boolean|null, "structure": one of ["active","passive",null], "expense_ratio_pct": number|null, "confidence": number}}
Source URL: {source_url}
Document markdown:
{_truncate(markdown)}"""
    return await _extract(prompt) or {"confidence": 0.0}
