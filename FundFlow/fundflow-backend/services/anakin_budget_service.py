"""Firestore-backed Anakin credit ledger, cache, and budget enforcement.

Degrades gracefully to in-memory storage when Firestore is unavailable so the app
runs locally without Firebase. All credit numbers are LOCALLY TRACKED estimates,
not Anakin's official balance.
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urlsplit, urlunsplit

from config import settings
from services.store_service import _get_db

logger = logging.getLogger("fundflow.budget")

EXTRACTION_VERSION = "v1"

# In-memory fallback stores
_mem_cache: Dict[str, Dict[str, Any]] = {}
_mem_usage: List[Dict[str, Any]] = []
_mem_budget: Dict[str, Any] = {"estimated_credits_used": 0}
_idempotency: Dict[str, str] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def cache_key(url: str, extraction_version: str = EXTRACTION_VERSION) -> str:
    norm = normalize_url(url)
    return hashlib.sha256(f"{norm}::{extraction_version}".encode()).hexdigest()[:32]


# ----------------------- Cache -----------------------

def get_cached(url: str, ttl_hours: Optional[int] = None,
               extraction_version: str = EXTRACTION_VERSION) -> Optional[Dict[str, Any]]:
    ttl = ttl_hours if ttl_hours is not None else settings.ANAKIN_CACHE_TTL_HOURS
    key = cache_key(url, extraction_version)
    entry = _read_cache_entry(key)
    if not entry:
        return None
    cached_at = entry.get("cached_at")
    if cached_at:
        try:
            ts = datetime.fromisoformat(cached_at)
            if datetime.now(timezone.utc) - ts > timedelta(hours=ttl):
                return None
        except ValueError:
            return None
    return entry


def set_cached(url: str, markdown: Optional[str], meta: Optional[dict] = None,
               extraction_version: str = EXTRACTION_VERSION) -> None:
    key = cache_key(url, extraction_version)
    entry = {
        "cache_key": key,
        "url": normalize_url(url),
        "extraction_version": extraction_version,
        "markdown": markdown,
        "meta": meta or {},
        "cached_at": _now(),
    }
    db = _get_db()
    if db:
        try:
            db.collection("anakin_cache").document(key).set(entry)
            return
        except Exception as e:
            logger.warning(f"cache write fell back to memory: {e}")
    _mem_cache[key] = entry


def _read_cache_entry(key: str) -> Optional[Dict[str, Any]]:
    db = _get_db()
    if db:
        try:
            doc = db.collection("anakin_cache").document(key).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.warning(f"cache read fell back to memory: {e}")
    return _mem_cache.get(key)


# ----------------------- Usage ledger -----------------------

def record_usage(*, user_id: str, scheme_code: Optional[str], audit_id: Optional[str],
                 operation: str, target: str, estimated_credits: int,
                 actual_credits: Optional[float] = None, cached: bool = False,
                 success: bool = True, job_id: Optional[str] = None) -> None:
    usage_id = hashlib.sha256(f"{audit_id}{operation}{target}{time.time()}".encode()).hexdigest()[:24]
    entry = {
        "usage_id": usage_id,
        "timestamp": _now(),
        "user_id": user_id,
        "scheme_code": scheme_code,
        "audit_id": audit_id,
        "operation": operation,            # scraper | wire | search
        "target": target,                  # url or action id
        "estimated_credits": estimated_credits,
        "actual_credits": actual_credits,
        "cached": cached,
        "success": success,
        "job_id": job_id,
    }
    _mem_usage.append(entry)
    if not cached and success:
        _mem_budget["estimated_credits_used"] = _mem_budget.get("estimated_credits_used", 0) + estimated_credits


def get_estimated_credits_used() -> int:
    db = _get_db()
    if db:
        try:
            doc = db.collection("anakin_budget").document("current").get()
            if doc.exists:
                return int(doc.to_dict().get("estimated_credits_used", 0))
            return 0
        except Exception as e:
            logger.warning(f"budget read fell back to memory: {e}")
    return int(_mem_budget.get("estimated_credits_used", 0))


def _recent_usage(limit: int = 20) -> List[Dict[str, Any]]:
    db = _get_db()
    if db:
        try:
            docs = (db.collection("anakin_usage")
                    .order_by("timestamp", direction="DESCENDING").limit(limit).stream())
            return [d.to_dict() for d in docs]
        except Exception as e:
            logger.warning(f"usage read fell back to memory: {e}")
    return list(reversed(_mem_usage[-limit:]))


# ----------------------- Budget enforcement -----------------------

class BudgetError(Exception):
    """Raised when a planned operation would exceed the configured budget."""


def check_budget(estimated_credits: int) -> None:
    """Raise BudgetError if running this would exceed the total configured budget."""
    used = get_estimated_credits_used()
    if used + estimated_credits > settings.ANAKIN_TOTAL_CREDIT_BUDGET:
        raise BudgetError(
            f"The audit was stopped to protect your Anakin credit budget "
            f"(locally tracked {used}/{settings.ANAKIN_TOTAL_CREDIT_BUDGET})."
        )
    if estimated_credits > settings.ANAKIN_MAX_CREDITS_PER_AUDIT:
        raise BudgetError(
            f"Estimated cost ({estimated_credits}) exceeds the per-audit limit "
            f"({settings.ANAKIN_MAX_CREDITS_PER_AUDIT})."
        )


# ----------------------- Idempotency -----------------------

def idempotency_get(key: str) -> Optional[str]:
    db = _get_db()
    if db:
        try:
            doc = db.collection("anakin_idempotency").document(key).get()
            if doc.exists:
                return doc.to_dict().get("audit_id")
            return None
        except Exception:
            pass
    return _idempotency.get(key)


def idempotency_set(key: str, audit_id: str) -> None:
    db = _get_db()
    if db:
        try:
            db.collection("anakin_idempotency").document(key).set(
                {"audit_id": audit_id, "created_at": _now()})
            return
        except Exception:
            pass
    _idempotency[key] = audit_id


# ----------------------- Usage report (admin endpoint) -----------------------

def usage_report() -> Dict[str, Any]:
    recent = _recent_usage(20)
    db = _get_db()
    today = datetime.now(timezone.utc).date().isoformat()
    all_usage = recent
    if not db:
        all_usage = list(reversed(_mem_usage[-500:]))
    by_op: Dict[str, int] = {}
    credits_today = 0
    cache_hits = 0
    total = 0
    for u in all_usage:
        total += 1
        op = u.get("operation", "unknown")
        by_op[op] = by_op.get(op, 0) + 1
        if u.get("cached"):
            cache_hits += 1
        ts = u.get("timestamp", "")
        if ts.startswith(today) and not u.get("cached"):
            credits_today += int(u.get("estimated_credits", 0) or 0)
    cache_rate = round(cache_hits / total, 3) if total else 0.0
    return {
        "label": "Locally tracked Anakin usage",
        "configured_budget": settings.ANAKIN_TOTAL_CREDIT_BUDGET,
        "estimated_credits_used": get_estimated_credits_used(),
        "estimated_credits_today": credits_today,
        "calls_by_operation": by_op,
        "cache_hit_rate": cache_rate,
        "recent_calls": recent,
    }
