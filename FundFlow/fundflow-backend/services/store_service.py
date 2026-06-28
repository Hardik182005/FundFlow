"""In-memory persistence store for FundFlow.

Firebase/Firestore has been removed — the app runs with a process-local in-memory
store. `_get_db()` always returns None so every service that consults it uses its own
in-memory fallback. Portfolios are kept here and seeded from the demo fixture.

Note: data does not persist across process restarts. Swap this module for a real
database implementation (same function signatures) if durable storage is needed.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("fundflow.store")

# process-local portfolio store: user_id -> {"user_id", "holdings": [...]}
_portfolios: Dict[str, Dict] = {}
_seeded = False


def _get_db():
    """S3-backed persistence when AUDIT_S3_BUCKET is set; else None (in-memory).

    Returning an S3 client lets audit results, the Anakin scrape cache, and the
    idempotency keys survive across Lambda invocations — so a repeated audit of a
    warmed fund returns instantly (well within the API Gateway 30s window).
    """
    try:
        from services.s3_store import get_db
        return get_db()
    except Exception as e:
        logger.warning(f"S3 store unavailable, using in-memory: {e}")
        return None


def _seed_demo() -> None:
    global _seeded
    if _seeded:
        return
    _seeded = True
    try:
        from services import demo_service
        if demo_service.enabled():
            p = demo_service.demo_portfolio()
            if p and p.get("user_id"):
                _portfolios.setdefault(p["user_id"], {"user_id": p["user_id"], "holdings": p.get("holdings", [])})
    except Exception as e:
        logger.warning(f"demo portfolio seed skipped: {e}")


async def save_portfolio(user_id: str, holdings: List[Dict]) -> bool:
    _portfolios[user_id] = {"user_id": user_id, "holdings": holdings}
    return True


async def get_portfolio(user_id: str) -> Optional[Dict]:
    _seed_demo()
    return _portfolios.get(user_id)


async def get_all_scheme_codes() -> List[str]:
    _seed_demo()
    codes = set()
    for data in _portfolios.values():
        for h in data.get("holdings", []):
            if h.get("scheme_code"):
                codes.add(h["scheme_code"])
    return list(codes)


async def update_portfolio_nav_snapshots(refreshed_navs: Dict) -> None:
    if not refreshed_navs:
        return
    from datetime import datetime
    for data in _portfolios.values():
        for h in data.get("holdings", []):
            code = h.get("scheme_code")
            if code and code in refreshed_navs:
                h["last_known_nav"] = refreshed_navs[code]["nav"]
                h["last_nav_date"] = refreshed_navs[code]["nav_date"]
        data["nav_snapshot_at"] = datetime.now().isoformat()
