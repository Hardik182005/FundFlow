"""Deterministic audit checks and trust scoring (no LLM, fully unit-testable).

All numeric comparisons happen here in Python. Each function returns a plain dict
that the pipeline wraps into an AuditCheckResult. Missing data yields
status="insufficient_data" — never a fabricated pass/fail.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

DIRECTIONAL_THRESHOLD_PP = 1.0  # percentage points

# direction -> expected sign of delta (+1 increase, -1 decrease, 0 none)
_EXPECTED_SIGN = {
    "increase": 1, "overweight": 1,
    "decrease": -1, "underweight": -1, "avoid": -1,
    "maintain": 0, "unknown": 0,
}

VERDICT_BANDS = [
    (80, "TRUSTED"), (65, "MONITOR"), (45, "REVIEW"), (0, "HIGH CONCERN"),
]


def verdict_for_score(score: float) -> str:
    for threshold, label in VERDICT_BANDS:
        if score >= threshold:
            return label
    return "HIGH CONCERN"


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def _match_sector(claim_sector: str, allocations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    cs = _norm(claim_sector)
    if not cs:
        return None
    for a in allocations:
        an = _norm(a.get("name"))
        if an == cs or cs in an or an in cs:
            return a
    # token overlap fallback
    cs_tokens = set(cs.split())
    best, best_overlap = None, 0
    for a in allocations:
        overlap = len(cs_tokens & set(_norm(a.get("name")).split()))
        if overlap > best_overlap:
            best, best_overlap = a, overlap
    return best if best_overlap else None


# ----------------------- Allocation diff -----------------------

def build_allocation_diff(current: List[Dict[str, Any]],
                          previous: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Join current & previous allocation lists by name; compute delta (pp)."""
    prev_map = {_norm(p.get("name")): p for p in previous}
    cur_map = {_norm(c.get("name")): c for c in current}
    names = list(dict.fromkeys(list(cur_map.keys()) + list(prev_map.keys())))
    out = []
    for n in names:
        c = cur_map.get(n)
        p = prev_map.get(n)
        cw = c.get("weight") if c else None
        pw = p.get("weight") if p else None
        delta = round(cw - pw, 2) if (cw is not None and pw is not None) else None
        out.append({
            "name": (c or p).get("name"),
            "current_weight": cw,
            "previous_weight": pw,
            "delta_percentage_points": delta,
            "classification": (c or p).get("market_cap_segment"),
        })
    return out


# ----------------------- Check 1: Manager Said vs Did -----------------------

def check_manager_said_vs_did(claims: List[Dict[str, Any]],
                              allocation_diff: List[Dict[str, Any]],
                              threshold_pp: float = DIRECTIONAL_THRESHOLD_PP) -> Dict[str, Any]:
    if not claims:
        return _insufficient("manager_said_vs_did", "Manager Said vs Did",
                             "No portfolio-action statements were found in the manager commentary.")
    if not any(a.get("delta_percentage_points") is not None for a in allocation_diff):
        return _insufficient("manager_said_vs_did", "Manager Said vs Did",
                             "Current and previous allocations could not both be retrieved, so statements could not be verified.")

    rows: List[Dict[str, Any]] = []
    evaluated = 0
    mismatches = 0
    findings: List[str] = []
    for claim in claims:
        exp = _EXPECTED_SIGN.get(claim.get("direction", "unknown"), 0)
        match = _match_sector(claim.get("asset_or_sector", ""), allocation_diff)
        if not match or match.get("delta_percentage_points") is None:
            rows.append({**_claim_row(claim, match), "status": "insufficient_evidence"})
            continue
        if exp == 0:
            rows.append({**_claim_row(claim, match), "status": "opinion_only"})
            continue
        evaluated += 1
        delta = match["delta_percentage_points"]
        actual_sign = 1 if delta >= threshold_pp else (-1 if delta <= -threshold_pp else 0)
        consistent = (actual_sign == exp)
        status = "consistent" if consistent else "mismatch"
        if not consistent:
            mismatches += 1
            findings.append(
                f"{match['name']} allocation moved {('+' if delta >= 0 else '')}{delta} pp "
                f"(from {match.get('previous_weight')}% to {match.get('current_weight')}%) "
                f"despite a '{claim.get('direction')}' statement."
            )
        rows.append({**_claim_row(claim, match), "status": status})

    if evaluated == 0:
        res = _insufficient("manager_said_vs_did", "Manager Said vs Did",
                            "Statements were found but none could be matched to a measurable allocation movement.")
        res["table"] = rows
        return res

    consistent_count = evaluated - mismatches
    score = round(100 * consistent_count / evaluated, 1)
    status = "pass" if score >= 75 else ("warning" if score >= 50 else "fail")
    summary = f"{mismatches} of {evaluated} directional statements were not reflected in the portfolio."
    return {
        "check_id": "manager_said_vs_did",
        "name": "Manager Said vs Did",
        "status": status,
        "score": score,
        "summary": summary,
        "explanation": (
            "Each forward-looking portfolio-action statement from the manager commentary is matched to the "
            "observed sector/holding movement between the previous and current factsheet. A statement is an "
            f"execution gap when the observed move contradicts the stated direction by at least {threshold_pp} pp."
        ),
        "findings": findings,
        "confidence": 0.7,
        "methodology": (
            f"delta = current_weight - previous_weight; increase if delta >= +{threshold_pp} pp, "
            f"decrease if delta <= -{threshold_pp} pp; score = consistent/evaluated * 100."
        ),
        "table": rows,
    }


def _claim_row(claim: Dict[str, Any], match: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "statement": claim.get("quoted_text") or claim.get("normalized_claim"),
        "direction": claim.get("direction"),
        "sector": claim.get("asset_or_sector"),
        "previous_weight": match.get("previous_weight") if match else None,
        "current_weight": match.get("current_weight") if match else None,
        "observed_movement": match.get("delta_percentage_points") if match else None,
    }


# ----------------------- Check 2: Style Drift -----------------------

def check_style_drift(mandate: Dict[str, Any], holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    seg_weights = {"large": 0.0, "mid": 0.0, "small": 0.0}
    classified = 0.0
    for h in holdings:
        seg = h.get("market_cap_segment")
        w = h.get("weight") or 0
        if seg in seg_weights:
            seg_weights[seg] += w
            classified += w

    min_large = mandate.get("min_largecap_pct")
    min_mid = mandate.get("min_midcap_pct")
    min_small = mandate.get("min_smallcap_pct")

    if classified < 30 or all(v is None for v in (min_large, min_mid, min_small)):
        return _insufficient("style_drift", "Style Drift",
                             "Either the mandate's market-cap floor or classified holdings were unavailable.")

    findings: List[str] = []
    breaches = 0
    checks = 0
    for seg, minimum, label in (("large", min_large, "large-cap"),
                                ("mid", min_mid, "mid-cap"),
                                ("small", min_small, "small-cap")):
        if minimum is None:
            continue
        checks += 1
        observed = round(seg_weights[seg], 1)
        if observed < minimum - 1.0:
            breaches += 1
            findings.append(f"Mandate requires minimum {minimum}% {label}; observed {observed}% (outside {round(minimum-observed,1)} pp).")

    if checks == 0:
        return _insufficient("style_drift", "Style Drift", "No comparable market-cap floor in the mandate.")

    if breaches == 0:
        status, score, summary = "pass", 90.0, "Observed allocation is consistent with the stated mandate."
    elif breaches == checks:
        status, score, summary = "fail", 35.0, "Observed allocation falls outside the stated mandate floor."
    else:
        status, score, summary = "warning", 60.0, "Potential style drift relative to the stated mandate."
    return {
        "check_id": "style_drift", "name": "Style Drift", "status": status, "score": score,
        "summary": summary,
        "explanation": "Compares the scheme's stated market-cap floor against the classified market-cap exposure of current holdings.",
        "findings": findings, "confidence": 0.6,
        "methodology": "Sum holding weights per market-cap segment; flag where observed < mandate minimum by >1 pp. Labelled 'potential style drift' unless regulatory definition is clear.",
        "observed": {k: round(v, 1) for k, v in seg_weights.items()},
        "mandate": {"min_large": min_large, "min_mid": min_mid, "min_small": min_small},
    }


# ----------------------- Check 3: Manager Tenure -----------------------

def check_manager_tenure(manager: Dict[str, Any], reference_date: Optional[str] = None) -> Dict[str, Any]:
    from datetime import datetime, timezone
    start = manager.get("manager_start_date")
    advertised = manager.get("advertised_return_periods") or []
    if not start:
        return _insufficient("manager_tenure", "Manager Continuity",
                             "Manager start date was not disclosed in the available documents.")
    parsed = _parse_date(start)
    if not parsed:
        return _insufficient("manager_tenure", "Manager Continuity",
                             f"Could not interpret the disclosed start date ('{start}').")
    now = datetime.now(timezone.utc)
    tenure_months = max(0, (now.year - parsed.year) * 12 + (now.month - parsed.month))

    advertises_5y = any("5" in str(p) and ("year" in str(p).lower() or "yr" in str(p).lower() or p.strip() in ("5Y", "5y")) for p in advertised)
    findings: List[str] = []
    if advertises_5y and tenure_months < 60:
        pct = round(100 * tenure_months / 60, 0)
        findings.append(f"The fund advertises a five-year return, but the current manager has managed it for {tenure_months} months (~{pct}% of that period).")

    if tenure_months >= 36:
        status, score, summary = "pass", 85.0, "Stable manager continuity."
    elif tenure_months >= 12:
        status, score, summary = "warning", 65.0, "Recent manager transition; track record partly reflects a prior manager."
    else:
        status, score, summary = "warning", 50.0, "Very recent manager transition."
    return {
        "check_id": "manager_tenure", "name": "Manager Continuity", "status": status, "score": score,
        "summary": summary,
        "explanation": "Measures how long the current manager has run the fund relative to the advertised return period.",
        "findings": findings, "confidence": 0.6,
        "methodology": "tenure_months = months since disclosed manager_start_date; compared to advertised return periods. No category percentile is invented.",
        "tenure_months": tenure_months,
    }


def _parse_date(s: str):
    from datetime import datetime
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%B %Y", "%b %Y", "%Y", "%b %d, %Y", "%d %B %Y", "%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    import re
    m = re.search(r"(20\d{2})", s)
    if m:
        try:
            return datetime(int(m.group(1)), 1, 1)
        except ValueError:
            return None
    return None


# ----------------------- Bonus: Skin in the Game -----------------------

def check_skin_in_game(skin: Dict[str, Any]) -> Dict[str, Any]:
    if not skin or not skin.get("disclosed"):
        return _insufficient("skin_in_game", "Skin in the Game",
                             "No manager investment disclosure was found in the available documents.")
    amount = skin.get("amount_invested")
    findings = [f"Manager investment disclosed as {amount} for {skin.get('disclosure_period') or 'the reporting period'}."]
    findings.append("This is an alignment signal, not a standalone measure of fund quality.")
    return {
        "check_id": "skin_in_game", "name": "Skin in the Game", "status": "pass", "score": 75.0,
        "summary": "Manager investment disclosure located.",
        "explanation": "Reports the manager's own disclosed investment in the scheme where available.",
        "findings": findings, "confidence": 0.5,
        "methodology": "Value quoted directly from the annual report / disclosure. Zero is not treated as misconduct.",
    }


# ----------------------- Bonus: Hidden Churn -----------------------

def check_hidden_churn(current: List[Dict[str, Any]], previous: List[Dict[str, Any]],
                       published_turnover_pct: Optional[float] = None,
                       reasonable_cap: float = 4.0) -> Dict[str, Any]:
    if not current or not previous:
        return _insufficient("hidden_churn", "Churn Transparency",
                             "Both current and previous holdings are required to estimate churn.")
    cur = {_norm(c.get("name")): (c.get("weight") or 0) / 100.0 for c in current}
    prev = {_norm(p.get("name")): (p.get("weight") or 0) / 100.0 for p in previous}
    names = set(cur) | set(prev)
    common_weight = sum(min(cur.get(n, 0), prev.get(n, 0)) for n in names)
    monthly_churn = max(0.0, 1 - common_weight)
    annualized = min(monthly_churn * 12, reasonable_cap)
    findings = [f"Observed holdings-change estimate (annualised): {round(annualized*100,0)}% based on portfolio overlap."]
    if published_turnover_pct is not None:
        findings.append(f"Published portfolio turnover ratio: {published_turnover_pct}% (indicator only; not the same formula).")
    return {
        "check_id": "hidden_churn", "name": "Churn Transparency", "status": "pass", "score": 70.0,
        "summary": "Observed holdings-change estimate computed from portfolio overlap.",
        "explanation": "Estimates portfolio change from the overlap between consecutive holdings snapshots.",
        "findings": findings, "confidence": 0.4,
        "methodology": "common = sum(min(cur,prev)); monthly_churn = 1 - common; annualised = min(monthly*12, cap). This is an observed estimate, NOT the official SEBI turnover formula.",
        "annualized_observed_churn_pct": round(annualized * 100, 1),
    }


# ----------------------- Check 4: NFO Clone Detector -----------------------

NFO_WEIGHTS = {"category": 0.20, "benchmark": 0.20, "mandate": 0.25,
               "sector": 0.20, "style": 0.10, "fee": 0.05}


def _sim_text(a, b) -> float:
    a, b = _norm(str(a or "")), _norm(str(b or ""))
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    return len(ta & tb) / max(1, len(ta | tb))


def check_nfo_clone(nfo: Dict[str, Any], universe: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not nfo or not universe:
        return _insufficient("nfo_clone", "NFO Clone Detector",
                             "No NFO document or comparison universe was available.")
    scored = []
    for fund in universe:
        s = (NFO_WEIGHTS["category"] * _sim_text(nfo.get("category"), fund.get("category"))
             + NFO_WEIGHTS["benchmark"] * _sim_text(nfo.get("benchmark"), fund.get("benchmark"))
             + NFO_WEIGHTS["mandate"] * _sim_text(nfo.get("market_cap_mandate"), fund.get("market_cap_mandate"))
             + NFO_WEIGHTS["sector"] * _sim_text(nfo.get("sector_or_theme"), fund.get("sector_or_theme"))
             + NFO_WEIGHTS["style"] * _sim_text(nfo.get("structure"), fund.get("structure")))
        fee = 0.0
        if nfo.get("expense_ratio_pct") is not None and fund.get("expense_ratio_pct") is not None:
            diff = abs(nfo["expense_ratio_pct"] - fund["expense_ratio_pct"])
            fee = max(0.0, 1 - diff)
        s += NFO_WEIGHTS["fee"] * fee
        scored.append({"name": fund.get("fund_name") or fund.get("name"),
                       "similarity": round(s * 100, 1),
                       "expense_ratio_pct": fund.get("expense_ratio_pct")})
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    top = scored[:3]
    close = [s for s in scored if s["similarity"] >= 70]
    best = top[0]["similarity"] if top else 0
    if best >= 80:
        status, score, verdict = "warning", 50.0, "Highly overlapping proposition"
    elif best >= 65:
        status, score, verdict = "warning", 65.0, "Similar to existing options"
    else:
        status, score, verdict = "pass", 85.0, "Distinct proposition"
    findings = [f"Compared against {len(universe)} funds currently available in the FundFlow comparison universe.",
                f"Closest match: {top[0]['name']} ({top[0]['similarity']}% similarity)." if top else "No close matches."]
    return {
        "check_id": "nfo_clone", "name": "NFO Clone Detector", "status": status, "score": score,
        "summary": f"{verdict}: {len(close)} closely comparable scheme(s).",
        "explanation": "Deterministic weighted similarity of the NFO proposition against a curated comparison universe.",
        "findings": findings, "confidence": 0.5,
        "methodology": "Weighted similarity — category 20%, benchmark 20%, mandate 25%, sector 20%, style 10%, fee 5%. Not an exhaustive comparison of every Indian fund.",
        "verdict_label": verdict, "closest": top,
    }


# ----------------------- helpers -----------------------

def _insufficient(check_id: str, name: str, reason: str) -> Dict[str, Any]:
    return {
        "check_id": check_id, "name": name, "status": "insufficient_data", "score": 0.0,
        "summary": reason, "explanation": reason, "findings": [], "confidence": 0.0,
        "methodology": "Marked insufficient_data; missing inputs are never converted into a pass or fail.",
    }


# ----------------------- Trust score -----------------------

DEFAULT_WEIGHTS = {
    "manager_said_vs_did": 35,
    "style_drift": 25,
    "manager_tenure": 15,
    "nfo_clone": 15,
    "skin_in_game": 5,
    "hidden_churn": 5,
}


def compute_trust_score(checks: List[Dict[str, Any]],
                        weights: Optional[Dict[str, int]] = None) -> Tuple[float, str]:
    weights = dict(weights or DEFAULT_WEIGHTS)
    present = {c["check_id"]: c for c in checks if c.get("status") != "insufficient_data"}
    # redistribute weight of absent/insufficient checks proportionally
    active = {cid: w for cid, w in weights.items() if cid in present}
    if not active:
        return 0.0, "REVIEW"
    total_w = sum(active.values())
    score = sum((present[cid]["score"] * w) for cid, w in active.items()) / total_w
    score = round(score, 1)
    return score, verdict_for_score(score)
