"""Fund source registry: verified source URLs per fund + low-cost validation.

Sources are seeded from config/fund_source_registry.json and may be overridden /
extended in Firestore (fund_sources/{scheme_code}) via the developer UI.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from services.store_service import _get_db
from services.anakin_client import anakin_client, AnakinError
from services import anakin_budget_service as budget

logger = logging.getLogger("fundflow.sources")

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "fund_source_registry.json")
_seed_cache: Optional[Dict[str, Any]] = None

_CAPTCHA_MARKERS = ("captcha", "are you a robot", "access denied", "request blocked",
                    "enable javascript", "verify you are human", "403 forbidden")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_seed() -> Dict[str, Any]:
    global _seed_cache
    if _seed_cache is None:
        try:
            with open(os.path.abspath(_REGISTRY_PATH), "r", encoding="utf-8") as f:
                _seed_cache = json.load(f).get("funds", {})
        except Exception as e:
            logger.warning(f"fund source seed load failed: {e}")
            _seed_cache = {}
    return _seed_cache


def list_funds() -> List[Dict[str, Any]]:
    merged: Dict[str, Any] = {k: dict(v) for k, v in _load_seed().items()}
    db = _get_db()
    if db:
        try:
            for doc in db.collection("fund_sources").stream():
                merged[doc.id] = doc.to_dict()
        except Exception as e:
            logger.warning(f"fund source list fell back to seed: {e}")
    return list(merged.values())


def get_fund(scheme_code: str) -> Optional[Dict[str, Any]]:
    db = _get_db()
    if db:
        try:
            doc = db.collection("fund_sources").document(scheme_code).get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            logger.warning(f"fund source read fell back to seed: {e}")
    return _load_seed().get(scheme_code)


def upsert_fund(scheme_code: str, data: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(data)
    data["scheme_code"] = scheme_code
    data["updated_at"] = _now()
    db = _get_db()
    if db:
        try:
            db.collection("fund_sources").document(scheme_code).set(data, merge=True)
        except Exception as e:
            logger.warning(f"fund source upsert failed: {e}")
    else:
        _load_seed()[scheme_code] = data
    return data


def available_documents(fund: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Return the document-type -> url map that is actually populated."""
    keys = ["factsheet_current_url", "factsheet_previous_url", "manager_commentary_url",
            "sid_url", "annual_report_url", "manager_profile_url", "nfo_document_url"]
    return {k: fund.get(k) for k in keys if fund.get(k)}


async def validate_source(url: str, user_id: str = "developer") -> Dict[str, Any]:
    """Run a low-cost basic Anakin scrape and report content health (cached)."""
    if not url:
        return {"url": url, "valid": False, "reason": "No URL provided."}

    cached = budget.get_cached(url, ttl_hours=720)
    if cached and cached.get("markdown"):
        md = cached["markdown"]
        return _assess(url, md, cached=True)

    if not anakin_client.configured:
        return {"url": url, "valid": False, "reason": "Anakin is not configured."}

    try:
        budget.check_budget(1)
    except budget.BudgetError as e:
        return {"url": url, "valid": False, "reason": str(e)}

    try:
        result = await anakin_client.scrape_url(url, use_browser=False)
    except AnakinError as e:
        return {"url": url, "valid": False, "reason": str(e)}

    md = result.markdown or ""
    success = result.status == "completed" and bool(md.strip())
    budget.record_usage(user_id=user_id, scheme_code=None, audit_id=None,
                        operation="scraper", target=url, estimated_credits=1,
                        cached=result.cached, success=success, job_id=result.job_id)
    if success and not result.cached:
        budget.set_cached(url, md, meta={"validated_at": _now(), "job_id": result.job_id})
    if not success:
        return {"url": url, "valid": False, "reason": result.error or "Empty content returned."}
    return _assess(url, md, cached=result.cached, job_id=result.job_id)


def _assess(url: str, markdown: str, cached: bool, job_id: Optional[str] = None) -> Dict[str, Any]:
    low = markdown.lower()
    captcha = any(m in low for m in _CAPTCHA_MARKERS) and len(markdown) < 2000
    title = ""
    for line in markdown.splitlines():
        s = line.strip().lstrip("#").strip()
        if s:
            title = s[:140]
            break
    # crude reporting-month detection
    month = None
    import re
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}", markdown)
    if m:
        month = m.group(0)
    return {
        "url": url,
        "valid": (not captcha) and len(markdown.strip()) > 200,
        "captcha_suspected": captcha,
        "content_length": len(markdown),
        "title": title,
        "reporting_period": month,
        "cached": cached,
        "anakin_job_id": job_id,
    }
