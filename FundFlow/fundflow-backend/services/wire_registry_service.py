"""Wire action discovery + registry.

Maps logical purposes (fund_profile, fund_holdings, fund_manager_news,
security_profile, security_market_cap, nfo_news) to concrete, *discovered* Anakin
Wire action IDs. Never fabricates an action ID:

Resolution order for a logical action:
    1. WIRE_ACTION_* environment override (settings.WIRE_ACTION_OVERRIDES)
    2. Firestore wire_action_registry/{logical_name}
    3. config/wire_actions_default.json (seeded from a real wire_discover run)

Discovery (POST /api/anakin/discover-wire-actions) searches the live catalog,
ranks candidates per logical purpose, and persists the best match.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from config import settings
from services.store_service import _get_db
from services.anakin_client import anakin_client, AnakinError

logger = logging.getLogger("fundflow.wire")

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "wire_actions_default.json")

# Natural-language intents used during discovery, per logical purpose.
DISCOVERY_QUERIES: Dict[str, List[str]] = {
    "fund_profile": ["mutual fund detail morningstar india", "mutual fund profile india"],
    "fund_holdings": ["mutual fund holdings portfolio india", "mutual fund portfolio morningstar"],
    "fund_manager_news": ["economic times mutual funds", "mutual fund manager news india"],
    "nfo_news": ["new fund offer nfo news india", "economic times mutual funds"],
    "security_profile": ["nse india stock profile", "company profile india stock"],
    "security_market_cap": ["bse india stock quote market cap", "company market capitalization india"],
}

_ENV_KEY = {
    "fund_profile": "fund_profile",
    "fund_holdings": "fund_holdings",
    "fund_manager_news": "fund_manager_news",
    "security_profile": "security_profile",
    "security_market_cap": "security_market_cap",
}

_defaults_cache: Optional[Dict[str, Any]] = None


def _load_defaults() -> Dict[str, Any]:
    global _defaults_cache
    if _defaults_cache is None:
        try:
            with open(os.path.abspath(_CONFIG_PATH), "r", encoding="utf-8") as f:
                _defaults_cache = json.load(f).get("logical_actions", {})
        except Exception as e:
            logger.warning(f"wire defaults load failed: {e}")
            _defaults_cache = {}
    return _defaults_cache


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_action(logical_name: str) -> Optional[Dict[str, Any]]:
    """Resolve a logical action to a concrete action record (or None)."""
    # 1. env override
    override = settings.WIRE_ACTION_OVERRIDES.get(_ENV_KEY.get(logical_name, logical_name))
    if override:
        return {"action_id": override, "logical_name": logical_name, "source": "env_override"}

    # 2. firestore
    db = _get_db()
    if db:
        try:
            doc = db.collection("wire_action_registry").document(logical_name).get()
            if doc.exists:
                rec = doc.to_dict()
                if rec.get("action_id"):
                    rec["source"] = "firestore"
                    return rec
        except Exception as e:
            logger.warning(f"wire registry read fell back to defaults: {e}")

    # 3. seeded defaults (real discovered IDs)
    rec = _load_defaults().get(logical_name)
    if rec and rec.get("action_id"):
        out = dict(rec)
        out["logical_name"] = logical_name
        out["source"] = "default_config"
        return out
    return None


def list_actions() -> Dict[str, Any]:
    out = {}
    for name in DISCOVERY_QUERIES.keys():
        out[name] = get_action(name)
    return out


def _persist(logical_name: str, rec: Dict[str, Any]) -> None:
    db = _get_db()
    if not db:
        return
    try:
        db.collection("wire_action_registry").document(logical_name).set(rec)
    except Exception as e:
        logger.warning(f"wire registry persist failed for {logical_name}: {e}")


def _score_candidate(logical_name: str, action: Any) -> float:
    """Heuristic ranking. Reject actions whose cost exceeds the per-call cap."""
    cost = action.credits_per_call or 1
    if cost > settings.ANAKIN_MAX_WIRE_CREDITS_PER_CALL:
        return -1.0
    catalog = (action.catalog or "").lower()
    name = (action.name or "").lower()
    score = 1.0
    hints = {
        "fund_profile": ["morningstar", "fund", "mutual"],
        "fund_holdings": ["portfolio", "holding", "morningstar"],
        "fund_manager_news": ["economic", "times", "news", "mutual"],
        "nfo_news": ["economic", "times", "nfo", "news"],
        "security_profile": ["nse", "stock", "profile"],
        "security_market_cap": ["bse", "quote", "market", "cap"],
    }.get(logical_name, [])
    for h in hints:
        if h in catalog or h in name:
            score += 1.0
    score -= 0.1 * cost
    return score


async def discover_wire_actions(logical_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Search the live Wire catalog and persist the best action per logical purpose.

    Returns a report. Falls back to seeded defaults when Anakin is unavailable so the
    registry is never left empty.
    """
    targets = logical_names or list(DISCOVERY_QUERIES.keys())
    report: Dict[str, Any] = {"discovered": {}, "fallbacks": [], "anakin_configured": anakin_client.configured}

    for logical in targets:
        chosen = None
        if anakin_client.configured:
            for q in DISCOVERY_QUERIES.get(logical, []):
                try:
                    actions = await anakin_client.search_wire_actions(q)
                except AnakinError as e:
                    logger.warning(f"wire search failed for '{q}': {e}")
                    continue
                ranked = sorted(
                    ((_score_candidate(logical, a), a) for a in actions),
                    key=lambda t: t[0], reverse=True,
                )
                ranked = [(s, a) for s, a in ranked if s >= 0 and a.action_id]
                if ranked:
                    best = ranked[0][1]
                    chosen = {
                        "action_id": best.action_id,
                        "catalog": best.catalog,
                        "name": best.name,
                        "description": best.description,
                        "param_schema": best.param_schema,
                        "output_schema": best.output_schema,
                        "credits_per_call": best.credits_per_call,
                        "logical_name": logical,
                        "discovered_at": _now(),
                        "source": "discovery",
                    }
                    break
        if not chosen:
            seeded = _load_defaults().get(logical)
            if seeded:
                report["fallbacks"].append(logical)
                chosen = dict(seeded)
                chosen.update({"logical_name": logical, "discovered_at": _now(), "source": "default_config"})
        if chosen:
            _persist(logical, chosen)
            report["discovered"][logical] = chosen
    return report
