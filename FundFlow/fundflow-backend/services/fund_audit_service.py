"""FundFlow Audit pipeline orchestrator.

Flow: validate -> estimate credits -> budget check -> load cache / scrape via Anakin
Universal Scraper -> Gemini extraction -> one Wire reality action -> deterministic
checks -> trust score -> evidence-linked verdict -> persist -> return.

Every external web fetch goes through Anakin (anakin_client). AMFI/mfapi NAV stays in
the existing pipeline. Numbers are computed in Python (audit_checks), never by the LLM.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from config import settings
from services.store_service import _get_db
from services.anakin_client import anakin_client, AnakinError, InsufficientCreditError
from services import anakin_budget_service as budget
from services import audit_extraction_service as extract
from services import audit_checks as checks
from services import fund_source_service as sources
from services import wire_registry_service as wire_reg

logger = logging.getLogger("fundflow.audit")

DISCLAIMER = (
    "This is an AI-assisted document and portfolio consistency audit, not investment "
    "advice. Verify source documents and consult a SEBI-registered investment adviser "
    "before making financial decisions."
)

# document_type -> source-registry key
_DOC_KEYS = {
    "factsheet_current": "factsheet_current_url",
    "factsheet_previous": "factsheet_previous_url",
    "manager_commentary": "manager_commentary_url",
    "sid": "sid_url",
    "annual_report": "annual_report_url",
    "manager_profile": "manager_profile_url",
    "nfo_document": "nfo_document_url",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evidence_id(url: str, doc_type: str) -> str:
    return hashlib.sha256(f"{doc_type}::{url}".encode()).hexdigest()[:16]


def _resolve_sources(req) -> Dict[str, str]:
    """Merge custom_sources (user-pasted) over the registry entry."""
    fund = sources.get_fund(req.scheme_code) or {}
    resolved: Dict[str, str] = {}
    for doc_type, key in _DOC_KEYS.items():
        url = None
        if req.custom_sources:
            url = getattr(req.custom_sources, key, None)
        if not url:
            url = fund.get(key)
        if url:
            resolved[doc_type] = url
    return resolved, fund


async def _get_document(doc_type: str, url: str, *, user_id: str, scheme_code: str,
                        audit_id: str, force_refresh: bool, usage: Dict[str, Any]) -> Dict[str, Any]:
    """Return {markdown, cached, job_id, url, doc_type} using cache then Anakin."""
    if not force_refresh:
        cached = budget.get_cached(url, ttl_hours=settings.ANAKIN_CACHE_TTL_HOURS)
        if cached and cached.get("markdown"):
            usage["cache_hits"] += 1
            budget.record_usage(user_id=user_id, scheme_code=scheme_code, audit_id=audit_id,
                                operation="scraper", target=url, estimated_credits=0,
                                cached=True, success=True, job_id=(cached.get("meta") or {}).get("job_id"))
            return {"doc_type": doc_type, "url": url, "markdown": cached["markdown"],
                    "cached": True, "job_id": (cached.get("meta") or {}).get("job_id")}

    if not anakin_client.configured:
        return {"doc_type": doc_type, "url": url, "markdown": None, "cached": False,
                "job_id": None, "error": "Anakin is not configured."}

    result = await anakin_client.scrape_url(url, use_browser=False)
    # browser fallback when normal scrape returns too little
    if result.status == "completed" and (not result.markdown or len(result.markdown.strip()) < 200):
        result = await anakin_client.scrape_url(url, use_browser=True)

    success = result.status == "completed" and bool((result.markdown or "").strip())
    usage["scraper_calls"] += 1
    if success and not result.cached:
        usage["fresh_calls"] += 1
        if result.job_id:
            usage["job_ids"].append(result.job_id)
        budget.set_cached(url, result.markdown, meta={"job_id": result.job_id, "scraped_at": _now()})
    elif result.cached:
        usage["cache_hits"] += 1
    budget.record_usage(user_id=user_id, scheme_code=scheme_code, audit_id=audit_id,
                        operation="scraper", target=url,
                        estimated_credits=0 if result.cached else 1,
                        cached=result.cached, success=success, job_id=result.job_id)
    return {"doc_type": doc_type, "url": url, "markdown": result.markdown if success else None,
            "cached": result.cached, "job_id": result.job_id,
            "error": None if success else (result.error or "No content returned.")}


def estimate_credits(resolved: Dict[str, str], force_refresh: bool) -> Dict[str, Any]:
    """Count uncached fresh scrapes + one wire action. Cap at MAX_FRESH_SCRAPER_URLS."""
    fresh = 0
    cached = 0
    for url in resolved.values():
        if not force_refresh and budget.get_cached(url):
            cached += 1
        else:
            fresh += 1
    fresh = min(fresh, settings.MAX_FRESH_SCRAPER_URLS)
    wire = 1 if wire_reg.get_action("fund_holdings") else 0
    wire_cost = 2  # morningstar portfolio ~2 credits; capped by MAX_WIRE_CREDITS_PER_CALL
    estimated = fresh * 1 + (wire_cost if wire else 0)
    return {"fresh_scrapes": fresh, "cached_documents": cached, "wire_actions": wire,
            "estimated_credits": estimated}


async def _run_wire_reality(fund: Dict[str, Any], usage: Dict[str, Any], *,
                            user_id: str, scheme_code: str, audit_id: str) -> Optional[Dict[str, Any]]:
    """Execute ONE reality-layer Wire action (fund holdings preferred)."""
    action = wire_reg.get_action("fund_holdings")
    ms = (fund or {}).get("morningstar") or {}
    if not action or not anakin_client.configured or not ms.get("fund_slug"):
        return None
    cost = action.get("credits_per_call") or 2
    if cost > settings.ANAKIN_MAX_WIRE_CREDITS_PER_CALL:
        return None
    params = {"share_class_slug": ms.get("share_class_slug") or ms.get("fund_id"),
              "fund_slug": ms.get("fund_slug")}
    try:
        res = await anakin_client.execute_wire_and_wait(action["action_id"], params, timeout_seconds=60)
    except Exception as e:  # wire is optional — never let it crash the audit
        logger.warning(f"wire reality action failed: {e}")
        return None
    success = res.status == "completed"
    usage["wire_calls"] += 1
    if success and res.job_id:
        usage["job_ids"].append(res.job_id)
    budget.record_usage(user_id=user_id, scheme_code=scheme_code, audit_id=audit_id,
                        operation="wire", target=action["action_id"],
                        estimated_credits=cost if success else 0, cached=False,
                        success=success, job_id=res.job_id)
    if not success:
        return None
    return {"action_id": action["action_id"], "catalog": action.get("catalog"),
            "job_id": res.job_id, "data": res.data}


async def run_audit(req) -> Dict[str, Any]:
    audit_id = "aud_" + uuid.uuid4().hex[:12]
    user_id = req.user_id
    scheme_code = req.scheme_code

    # idempotency: same user+scheme+sources within budget guard
    idem_key = hashlib.sha256(f"{user_id}:{scheme_code}:{req.audit_type}:{req.force_refresh}".encode()).hexdigest()[:24]
    if not req.force_refresh:
        existing = budget.idempotency_get(idem_key)
        if existing:
            saved = get_audit(existing)
            if saved:
                logger.info(f"idempotent hit -> returning audit {existing}")
                return saved

    resolved, fund = _resolve_sources(req)
    fund = fund or {}
    fund_type = fund.get("fund_type", "equity")

    if not resolved:
        raise AuditError("This fund does not have enough source documents configured.")

    est = estimate_credits(resolved, req.force_refresh)
    try:
        budget.check_budget(est["estimated_credits"])
    except budget.BudgetError as e:
        raise AuditError(str(e), code=402)

    usage = {"scraper_calls": 0, "wire_calls": 0, "search_calls": 0,
             "fresh_calls": 0, "cache_hits": 0, "estimated_credits": 0, "job_ids": []}

    # cap fresh scrapes
    items = list(resolved.items())
    fresh_used = 0
    fetch_tasks = []
    for doc_type, url in items:
        is_cached = bool(budget.get_cached(url)) and not req.force_refresh
        if not is_cached:
            if fresh_used >= settings.MAX_FRESH_SCRAPER_URLS:
                continue
            fresh_used += 1
        fetch_tasks.append(_get_document(doc_type, url, user_id=user_id, scheme_code=scheme_code,
                                         audit_id=audit_id, force_refresh=req.force_refresh, usage=usage))
    docs = await asyncio.gather(*fetch_tasks)
    doc_map = {d["doc_type"]: d for d in docs if d.get("markdown")}

    # ---- Extraction (parallel) ----
    async def _safe(coro, default):
        try:
            return await coro
        except Exception as e:
            logger.warning(f"extraction step failed: {e}")
            return default

    cur_fs = doc_map.get("factsheet_current", {}).get("markdown")
    prev_fs = doc_map.get("factsheet_previous", {}).get("markdown")
    commentary = doc_map.get("manager_commentary", {}).get("markdown") or cur_fs
    sid = doc_map.get("sid", {}).get("markdown") or cur_fs
    profile = doc_map.get("manager_profile", {}).get("markdown") or cur_fs
    annual = doc_map.get("annual_report", {}).get("markdown")

    cur_url = doc_map.get("factsheet_current", {}).get("url", "")
    prev_url = doc_map.get("factsheet_previous", {}).get("url", "")

    tasks = {
        "claims": _safe(extract.extract_manager_claims(commentary or "", cur_url), []),
        "cur_sectors": _safe(extract.extract_sector_allocation(cur_fs or "", cur_url), []),
        "prev_sectors": _safe(extract.extract_sector_allocation(prev_fs or "", prev_url), []),
        "cur_holdings": _safe(extract.extract_holdings(cur_fs or "", cur_url), []),
        "prev_holdings": _safe(extract.extract_holdings(prev_fs or "", prev_url), []),
        "mandate": _safe(extract.extract_scheme_mandate(sid or "", cur_url), {}),
        "manager": _safe(extract.extract_manager_information(profile or "", cur_url), {}),
        "turnover": _safe(extract.extract_turnover_ratio(cur_fs or "", cur_url), {}),
    }
    if annual:
        tasks["skin"] = _safe(extract.extract_skin_in_game(annual, doc_map["annual_report"]["url"]), {})
    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values())))

    # ---- Wire reality layer ----
    wire_result = await _run_wire_reality(fund, usage, user_id=user_id, scheme_code=scheme_code, audit_id=audit_id)

    # ---- Deterministic checks ----
    sector_diff = checks.build_allocation_diff(results["cur_sectors"], results["prev_sectors"])
    holdings_diff = checks.build_allocation_diff(results["cur_holdings"], results["prev_holdings"])

    check_list: List[Dict[str, Any]] = []
    check_list.append(checks.check_manager_said_vs_did(results["claims"], sector_diff))
    check_list.append(checks.check_style_drift(results["mandate"], results["cur_holdings"]))
    check_list.append(checks.check_manager_tenure(results["manager"]))
    check_list.append(checks.check_skin_in_game(results.get("skin", {})))
    check_list.append(checks.check_hidden_churn(results["cur_holdings"], results["prev_holdings"],
                                                (results["turnover"] or {}).get("turnover_ratio_pct")))

    if req.audit_type == "nfo" or doc_map.get("nfo_document"):
        nfo = await _safe(extract.extract_nfo_mandate(doc_map.get("nfo_document", {}).get("markdown", "") or "", ""), {})
        universe = _comparison_universe()
        check_list.append(checks.check_nfo_clone(nfo, universe))

    trust_score, verdict = checks.compute_trust_score(check_list)

    # ---- Evidence ----
    evidence = []
    for doc_type, d in doc_map.items():
        md = d.get("markdown") or ""
        evidence.append({
            "id": _evidence_id(d["url"], doc_type),
            "source_type": doc_type,
            "title": _title_from(md, doc_type),
            "url": d["url"],
            "excerpt": md.strip()[:280] if md else None,
            "published_date": None,
            "reporting_period": _month_from(md),
            "scraped_at": _now(),
            "anakin_job_id": d.get("job_id"),
            "cached": d.get("cached", False),
            "extraction_confidence": 0.6,
        })
    if wire_result:
        evidence.append({
            "id": _evidence_id(wire_result["action_id"], "wire"),
            "source_type": "wire_reality",
            "title": f"Anakin Wire: {wire_result['catalog']}",
            "url": f"anakin-wire://{wire_result['action_id']}",
            "excerpt": "Reality-layer data retrieved via Anakin Wire.",
            "reporting_period": None, "scraped_at": _now(),
            "anakin_job_id": wire_result.get("job_id"), "cached": False, "extraction_confidence": 0.7,
        })

    limitations = _limitations(doc_map, results, wire_result)
    usage["estimated_credits"] = usage["fresh_calls"] + sum(
        1 for _ in range(0))  # base
    usage["estimated_credits"] = usage["fresh_calls"] + (2 if wire_result else 0)

    verdict_expl = _verdict_explanation(verdict, trust_score, check_list)

    audit = {
        "audit_id": audit_id, "scheme_code": scheme_code, "fund_name": req.fund_name,
        "fund_type": fund_type, "generated_at": _now(),
        "trust_score": trust_score, "verdict": verdict, "verdict_explanation": verdict_expl,
        "checks": check_list, "evidence": evidence,
        "manager_claims": results["claims"],
        "allocation_diff": sector_diff + holdings_diff,
        "anakin_usage": usage, "limitations": limitations,
        "disclaimer": DISCLAIMER, "is_demo": False,
        "wire_reality": {"action_id": wire_result["action_id"], "catalog": wire_result["catalog"]} if wire_result else None,
    }

    _save_audit(audit, user_id)
    budget.idempotency_set(idem_key, audit_id)
    return audit


def _comparison_universe() -> List[Dict[str, Any]]:
    """Curated comparison universe for the NFO check (from the source registry)."""
    out = []
    for f in sources.list_funds():
        out.append({"fund_name": f.get("fund_name"), "category": f.get("category"),
                    "benchmark": f.get("category"), "market_cap_mandate": f.get("category"),
                    "sector_or_theme": f.get("category"), "structure": "active",
                    "expense_ratio_pct": None})
    return out


def _title_from(md: str, doc_type: str) -> str:
    for line in (md or "").splitlines():
        s = line.strip().lstrip("#").strip()
        if s:
            return s[:140]
    return doc_type.replace("_", " ").title()


def _month_from(md: str) -> Optional[str]:
    import re
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}", md or "")
    return m.group(0) if m else None


def _limitations(doc_map, results, wire_result) -> List[str]:
    lim = []
    if "factsheet_previous" not in doc_map:
        lim.append("A previous factsheet was not available, so allocation movement checks may be limited.")
    if not results.get("claims"):
        lim.append("No explicit manager portfolio-action statements were found.")
    if not wire_result:
        lim.append("The reality-layer Wire action did not return data; conclusions rely on document evidence only.")
    return lim


def _verdict_explanation(verdict: str, score: float, check_list) -> str:
    failed = [c["name"] for c in check_list if c.get("status") == "fail"]
    warned = [c["name"] for c in check_list if c.get("status") == "warning"]
    parts = [f"Overall trust score {score}/100 ({verdict})."]
    if failed:
        parts.append("Execution gaps in: " + ", ".join(failed) + ".")
    if warned:
        parts.append("Areas to monitor: " + ", ".join(warned) + ".")
    if not failed and not warned:
        parts.append("No material statement-portfolio mismatches were detected in the available evidence.")
    return " ".join(parts)


# ----------------------- Persistence -----------------------

def _save_audit(audit: Dict[str, Any], user_id: str) -> None:
    db = _get_db()
    if not db:
        _MEM_AUDITS[audit["audit_id"]] = audit
        _MEM_USER_INDEX.setdefault(user_id, []).append(audit["audit_id"])
        return
    try:
        db.collection("fund_audits").document(audit["audit_id"]).set(audit)
        db.collection("audit_index").document(f"{user_id}_{audit['scheme_code']}").set(
            {"user_id": user_id, "scheme_code": audit["scheme_code"],
             "audit_id": audit["audit_id"], "generated_at": audit["generated_at"],
             "trust_score": audit["trust_score"], "verdict": audit["verdict"],
             "fund_name": audit["fund_name"]})
    except Exception as e:
        logger.warning(f"audit save fell back to memory: {e}")
        _MEM_AUDITS[audit["audit_id"]] = audit
        _MEM_USER_INDEX.setdefault(user_id, []).append(audit["audit_id"])


_MEM_AUDITS: Dict[str, Any] = {}
_MEM_USER_INDEX: Dict[str, List[str]] = {}


def get_audit(audit_id: str) -> Optional[Dict[str, Any]]:
    db = _get_db()
    if db:
        try:
            doc = db.collection("fund_audits").document(audit_id).get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            logger.warning(f"audit read fell back to memory: {e}")
    return _MEM_AUDITS.get(audit_id)


def latest_for_fund(scheme_code: str, user_id: str = "demo-user") -> Optional[Dict[str, Any]]:
    db = _get_db()
    if db:
        try:
            doc = db.collection("audit_index").document(f"{user_id}_{scheme_code}").get()
            if doc.exists:
                return get_audit(doc.to_dict().get("audit_id"))
        except Exception as e:
            logger.warning(f"latest_for_fund fell back to memory: {e}")
    for aid in reversed(_MEM_USER_INDEX.get(user_id, [])):
        a = _MEM_AUDITS.get(aid)
        if a and a.get("scheme_code") == scheme_code:
            return a
    return None


def audits_for_user(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    db = _get_db()
    if db:
        try:
            docs = (db.collection("audit_index").where("user_id", "==", user_id).stream())
            return sorted([d.to_dict() for d in docs], key=lambda x: x.get("generated_at", ""), reverse=True)[:limit]
        except Exception as e:
            logger.warning(f"audits_for_user fell back to memory: {e}")
    return [_summary(_MEM_AUDITS[a]) for a in reversed(_MEM_USER_INDEX.get(user_id, [])) if a in _MEM_AUDITS][:limit]


def _summary(a: Dict[str, Any]) -> Dict[str, Any]:
    return {"audit_id": a["audit_id"], "scheme_code": a["scheme_code"], "fund_name": a["fund_name"],
            "generated_at": a["generated_at"], "trust_score": a["trust_score"], "verdict": a["verdict"]}


class AuditError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code
