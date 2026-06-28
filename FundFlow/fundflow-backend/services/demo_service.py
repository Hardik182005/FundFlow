"""Demo mode: serve cached fixture audits/portfolio. Clearly labelled, never
silently substituted for live data."""
from __future__ import annotations

import json
import logging
import os
from typing import Optional, Dict, Any, List

from config import settings

logger = logging.getLogger("fundflow.demo")
_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "demo")
_cache: Dict[str, Any] = {}


def _load(name: str) -> Optional[Dict[str, Any]]:
    if name in _cache:
        return _cache[name]
    try:
        with open(os.path.abspath(os.path.join(_DIR, name)), "r", encoding="utf-8") as f:
            _cache[name] = json.load(f)
            return _cache[name]
    except Exception as e:
        logger.warning(f"demo fixture load failed ({name}): {e}")
        return None


def enabled() -> bool:
    return settings.DEMO_MODE


def get_demo_audit(audit_id: str) -> Optional[Dict[str, Any]]:
    a = _load("demo_audit_hdfc_midcap.json")
    if a and a.get("audit_id") == audit_id:
        return a
    return None


def demo_audit_summaries() -> List[Dict[str, Any]]:
    a = _load("demo_audit_hdfc_midcap.json")
    if not a:
        return []
    return [{"audit_id": a["audit_id"], "scheme_code": a["scheme_code"], "fund_name": a["fund_name"],
             "generated_at": a["generated_at"], "trust_score": a["trust_score"], "verdict": a["verdict"]}]


def demo_portfolio() -> Optional[Dict[str, Any]]:
    return _load("demo_portfolio.json")
