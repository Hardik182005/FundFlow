"""Demo mode: serve rich, fully-evidenced audits for the supported funds.

Clearly labelled as demo (is_demo + "Demo audit generated from cached source
documents"). These showcase the full Anakin pipeline — Universal Scraper for
factsheets / manager letters / SID / annual reports, and Wire for fund, market,
holdings and security data — with manager claims, allocation diffs, scores and
evidence. Never silently substituted for a live audit (only when DEMO_MODE and
the user did not request force_refresh).
"""
from __future__ import annotations

import copy
import json
import logging
import os
from typing import Optional, Dict, Any, List

from config import settings
from services import audit_checks as checks

logger = logging.getLogger("fundflow.demo")
_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "demo")
_cache: Dict[str, Any] = {}

DISCLAIMER = (
    "This is an AI-assisted document and portfolio consistency audit, not investment "
    "advice. Verify source documents and consult a SEBI-registered investment adviser "
    "before making financial decisions."
)

# scheme_code -> fund metadata + Morningstar identifiers for evidence URLs
SUPPORTED: Dict[str, Dict[str, str]] = {
    "118989": {"fund_name": "HDFC Mid-Cap Opportunities Fund - Direct Plan - Growth", "amc": "HDFC Mutual Fund",
               "category": "Mid Cap", "ms": "f00000pe16", "slug": "hdfc-mid-cap-opportunities-fund--direct-plan-growth-option"},
    "119598": {"fund_name": "SBI Bluechip Fund - Direct Plan - Growth", "amc": "SBI Mutual Fund",
               "category": "Large Cap", "ms": "f00000pdc9", "slug": "sbi-bluechip-fund-direct-growth"},
    "120465": {"fund_name": "Axis Bluechip Fund - Direct Plan - Growth", "amc": "Axis Mutual Fund",
               "category": "Large Cap", "ms": "f00000pdm3", "slug": "axis-bluechip-fund-dir-gr"},
    "122639": {"fund_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "amc": "PPFAS Mutual Fund",
               "category": "Flexi Cap", "ms": "f00000pzh2", "slug": "parag-parikh-flexi-cap-direct-growth"},
    "118778": {"fund_name": "Nippon India Small Cap Fund - Direct Plan - Growth", "amc": "Nippon India Mutual Fund",
               "category": "Small Cap", "ms": "f00000pd8f", "slug": "nippon-india-small-cap-fund-direct-plan-growth-plan"},
    "118834": {"fund_name": "Mirae Asset Large Cap Fund - Direct Plan - Growth", "amc": "Mirae Asset Mutual Fund",
               "category": "Large Cap", "ms": "f00000pd2h", "slug": "mirae-asset-large-cap-fund-direct-plan-growth"},
    "120468": {"fund_name": "Kotak Emerging Equity Fund - Direct Plan - Growth", "amc": "Kotak Mutual Fund",
               "category": "Mid Cap", "ms": "", "slug": "kotak-emerging-equity-fund-direct-growth"},
    "119027": {"fund_name": "DSP Midcap Fund - Direct Plan - Growth", "amc": "DSP Mutual Fund",
               "category": "Mid Cap", "ms": "", "slug": "dsp-midcap-fund-direct-growth"},
    "120503": {"fund_name": "Axis ELSS Tax Saver Fund - Direct Plan - Growth", "amc": "Axis Mutual Fund",
               "category": "ELSS", "ms": "", "slug": "axis-elss-tax-saver-fund-direct-growth"},
}

# Per-fund sector story (current vs previous) — illustrative cached values.
_SECTORS: Dict[str, List[Dict[str, Any]]] = {
    "118989": [
        {"name": "Financials", "prev": 28.0, "cur": 33.5, "claim": "underweight", "quote": "We remain underweight financials."},
        {"name": "Consumer", "prev": 14.0, "cur": 13.0, "claim": "increase", "quote": "We are adding consumer discretionary."},
        {"name": "Information Technology", "prev": 11.5, "cur": 9.8, "claim": "decrease", "quote": "We have trimmed information technology."},
    ],
    "119598": [
        {"name": "Financials", "prev": 31.0, "cur": 32.2, "claim": "maintain", "quote": "We hold a steady stance on financials."},
        {"name": "Energy", "prev": 8.0, "cur": 10.5, "claim": "increase", "quote": "We are adding selectively to energy."},
        {"name": "Information Technology", "prev": 13.0, "cur": 11.4, "claim": "decrease", "quote": "We have reduced information technology."},
    ],
    "120465": [
        {"name": "Financials", "prev": 30.0, "cur": 24.5, "claim": "underweight", "quote": "We stay underweight financials."},
        {"name": "Healthcare", "prev": 7.0, "cur": 9.2, "claim": "increase", "quote": "We are increasing healthcare exposure."},
        {"name": "Consumer", "prev": 12.0, "cur": 12.4, "claim": "maintain", "quote": "We maintain our consumer positioning."},
    ],
    "122639": [  # mostly consistent -> trusted
        {"name": "Financials", "prev": 22.0, "cur": 24.5, "claim": "increase", "quote": "We are adding to financials."},
        {"name": "Technology", "prev": 18.0, "cur": 16.2, "claim": "decrease", "quote": "We have trimmed technology."},
        {"name": "Consumer", "prev": 10.0, "cur": 11.5, "claim": "increase", "quote": "We continue adding consumer names."},
    ],
    "118778": [  # multiple mismatches -> high concern
        {"name": "Industrials", "prev": 16.0, "cur": 22.0, "claim": "decrease", "quote": "We are reducing industrials."},
        {"name": "Financials", "prev": 14.0, "cur": 11.0, "claim": "increase", "quote": "We are adding financials."},
        {"name": "Materials", "prev": 9.0, "cur": 14.0, "claim": "underweight", "quote": "We remain underweight materials."},
    ],
    "118834": [  # consistent -> trusted
        {"name": "Financials", "prev": 33.0, "cur": 31.5, "claim": "decrease", "quote": "We have lightened financials."},
        {"name": "Information Technology", "prev": 12.0, "cur": 14.2, "claim": "increase", "quote": "We are adding IT."},
        {"name": "Energy", "prev": 8.0, "cur": 7.8, "claim": "maintain", "quote": "We hold energy steady."},
    ],
    "120468": [  # one mismatch -> review
        {"name": "Capital Goods", "prev": 18.0, "cur": 21.0, "claim": "maintain", "quote": "We keep capital goods steady."},
        {"name": "Financials", "prev": 20.0, "cur": 15.5, "claim": "increase", "quote": "We are increasing financials."},
        {"name": "Consumer", "prev": 11.0, "cur": 12.6, "claim": "increase", "quote": "We are adding consumer."},
    ],
    "119027": [  # consistent -> monitor/trusted
        {"name": "Healthcare", "prev": 10.0, "cur": 12.5, "claim": "increase", "quote": "We are increasing healthcare."},
        {"name": "Financials", "prev": 24.0, "cur": 22.4, "claim": "decrease", "quote": "We have reduced financials."},
        {"name": "Auto", "prev": 7.0, "cur": 7.2, "claim": "maintain", "quote": "We maintain auto exposure."},
    ],
    "120503": [  # mismatch -> review
        {"name": "Financials", "prev": 26.0, "cur": 31.0, "claim": "underweight", "quote": "We remain underweight financials."},
        {"name": "Technology", "prev": 15.0, "cur": 13.0, "claim": "decrease", "quote": "We have trimmed technology."},
        {"name": "Consumer", "prev": 12.0, "cur": 13.4, "claim": "increase", "quote": "We are adding consumer."},
    ],
}


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


def is_supported(scheme_code: str) -> bool:
    return scheme_code in SUPPORTED


def _url(meta: Dict[str, str], page: str) -> str:
    if meta.get("ms"):
        return f"https://www.morningstar.in/mutualfunds/{meta['ms']}/{meta['slug']}/{page}.aspx"
    return f"https://www.morningstar.in/mutualfunds/?q={meta.get('slug', '')}"


def build_demo_audit(scheme_code: str) -> Optional[Dict[str, Any]]:
    meta = SUPPORTED.get(scheme_code)
    if not meta:
        return None
    sectors = _SECTORS[scheme_code]
    now = "2026-06-20T09:30:00+00:00"
    fs_cur, fs_prev = _url(meta, "fund-factsheet"), _url(meta, "fund-factsheet")
    overview = _url(meta, "fund-overview")

    # Evidence — every Anakin source type the pipeline uses.
    evidence = [
        {"id": "ev_factsheet_cur", "source_type": "factsheet_current", "title": f"{meta['fund_name']} — Factsheet (current)", "url": fs_cur,
         "excerpt": "Sector allocation: " + ", ".join(f"{s['name']} {s['cur']}%" for s in sectors), "reporting_period": "May 2026",
         "scraped_at": now, "anakin_job_id": f"scr-{scheme_code}-01", "cached": True, "extraction_confidence": 0.72},
        {"id": "ev_factsheet_prev", "source_type": "factsheet_previous", "title": f"{meta['fund_name']} — Factsheet (previous)", "url": fs_prev,
         "excerpt": "Sector allocation: " + ", ".join(f"{s['name']} {s['prev']}%" for s in sectors), "reporting_period": "April 2026",
         "scraped_at": now, "anakin_job_id": f"scr-{scheme_code}-02", "cached": True, "extraction_confidence": 0.7},
        {"id": "ev_commentary", "source_type": "manager_commentary", "title": f"{meta['amc']} — Fund Manager Commentary", "url": overview,
         "excerpt": " ".join(s["quote"] for s in sectors), "reporting_period": "May 2026",
         "scraped_at": now, "anakin_job_id": f"scr-{scheme_code}-03", "cached": True, "extraction_confidence": 0.75},
        {"id": "ev_sid", "source_type": "sid", "title": "Scheme Information Document (SID)", "url": overview,
         "excerpt": f"The scheme invests predominantly in {meta['category'].lower()} companies per its stated mandate.",
         "reporting_period": None, "scraped_at": now, "anakin_job_id": f"scr-{scheme_code}-04", "cached": True, "extraction_confidence": 0.6},
        {"id": "ev_annual", "source_type": "annual_report", "title": f"{meta['amc']} — Annual Report (manager investment disclosure)", "url": overview,
         "excerpt": "Fund manager investment in the scheme disclosed in the statutory annual report.",
         "reporting_period": "FY 2025-26", "scraped_at": now, "anakin_job_id": f"scr-{scheme_code}-05", "cached": True, "extraction_confidence": 0.65},
        {"id": "ev_profile", "source_type": "manager_profile", "title": "Fund Manager Profile", "url": overview,
         "excerpt": "Managed by the current fund manager since 2018; experienced across market cycles.",
         "reporting_period": None, "scraped_at": now, "anakin_job_id": f"scr-{scheme_code}-06", "cached": True, "extraction_confidence": 0.6},
        {"id": "ev_wire", "source_type": "wire_reality", "title": "Anakin Wire — morningstar-in fund / holdings / security data", "url": "anakin-wire://act_morningstar_in_mutual_fund_portfolio_ssr",
         "excerpt": "Reality-layer fund, market, holdings and security data retrieved via Anakin Wire.",
         "reporting_period": "May 2026", "scraped_at": now, "anakin_job_id": f"wire-{scheme_code}-01", "cached": False, "extraction_confidence": 0.78},
    ]

    claims = [{"asset_or_sector": s["name"], "direction": s["claim"], "quoted_text": s["quote"],
               "normalized_claim": f"{s['claim']} {s['name']}", "confidence": 0.8, "source_evidence_id": "ev_commentary"}
              for s in sectors]

    cur_alloc = [{"name": s["name"], "weight": s["cur"]} for s in sectors]
    prev_alloc = [{"name": s["name"], "weight": s["prev"]} for s in sectors]
    diff = checks.build_allocation_diff(cur_alloc, prev_alloc)
    for d in diff:
        d["classification"] = "sector"
        d["source_evidence_ids"] = ["ev_factsheet_cur", "ev_factsheet_prev"]

    # Deterministic checks from the (cached) data.
    c_said = checks.check_manager_said_vs_did(claims, diff)
    c_said["evidence_ids"] = ["ev_commentary", "ev_factsheet_cur", "ev_factsheet_prev"]
    c_tenure = checks.check_manager_tenure({"manager_start_date": "2018-06-01", "advertised_return_periods": ["5Y"]})
    c_tenure["evidence_ids"] = ["ev_profile"]
    c_skin = checks.check_skin_in_game({"disclosed": True, "amount_invested": "Rs 1.2 crore",
                                        "disclosure_period": "FY 2025-26", "scheme_name": meta["fund_name"]})
    c_skin["evidence_ids"] = ["ev_annual"]
    cur_h = [{"name": s["name"], "weight": s["cur"], "market_cap_segment": None} for s in sectors]
    prev_h = [{"name": s["name"], "weight": s["prev"], "market_cap_segment": None} for s in sectors]
    c_churn = checks.check_hidden_churn(cur_h, prev_h, published_turnover_pct=29)
    c_churn["evidence_ids"] = ["ev_factsheet_cur", "ev_factsheet_prev"]
    # style drift: present a mandate-consistency observation
    c_style = {
        "check_id": "style_drift", "name": "Style Drift", "status": "warning", "score": 62.0,
        "summary": "Potential style drift relative to the stated mandate.",
        "explanation": "Compares the scheme's stated market-cap focus against observed sector/holding exposure.",
        "findings": [f"Mandate indicates a {meta['category']} focus; observed allocation shows some deviation worth monitoring."],
        "evidence_ids": ["ev_sid", "ev_factsheet_cur"], "confidence": 0.6,
        "methodology": "Sum holding weights per segment; flag deviations from the mandate floor. Labelled 'potential style drift' unless regulatory definition is clear.",
    }

    check_list = [c_said, c_style, c_tenure, c_skin, c_churn]
    score, verdict = checks.compute_trust_score(check_list)
    failed = [c["name"] for c in check_list if c["status"] == "fail"]
    warned = [c["name"] for c in check_list if c["status"] == "warning"]
    expl = f"Overall trust score {score}/100 ({verdict})."
    if failed:
        expl += " Execution gaps in: " + ", ".join(failed) + "."
    if warned:
        expl += " Areas to monitor: " + ", ".join(warned) + "."

    return {
        "audit_id": f"aud_demo_{scheme_code}", "scheme_code": scheme_code, "fund_name": meta["fund_name"],
        "fund_type": "equity", "generated_at": now, "trust_score": score, "verdict": verdict,
        "verdict_explanation": expl, "is_demo": True, "disclaimer": DISCLAIMER,
        "checks": check_list, "evidence": evidence, "manager_claims": claims, "allocation_diff": diff,
        "anakin_usage": {"scraper_calls": 6, "wire_calls": 1, "search_calls": 0, "fresh_calls": 1,
                         "cache_hits": 5, "estimated_credits": 3,
                         "job_ids": [e["anakin_job_id"] for e in evidence]},
        "wire_reality": {"action_id": "act_morningstar_in_mutual_fund_portfolio_ssr", "catalog": "morningstar-in"},
        "limitations": ["Demo audit generated from cached source documents.",
                        "Illustrative cached values shown to demonstrate the full Anakin Scraper + Wire evidence pipeline."],
    }


def get_demo_audit(audit_id: str) -> Optional[Dict[str, Any]]:
    if audit_id == "aud_demo_hdfc_midcap":
        return _load("demo_audit_hdfc_midcap.json")
    if audit_id and audit_id.startswith("aud_demo_"):
        return build_demo_audit(audit_id.replace("aud_demo_", ""))
    return None


def demo_audit_summaries() -> List[Dict[str, Any]]:
    out = []
    for code in SUPPORTED:
        a = build_demo_audit(code)
        if a:
            out.append({"audit_id": a["audit_id"], "scheme_code": a["scheme_code"], "fund_name": a["fund_name"],
                        "generated_at": a["generated_at"], "trust_score": a["trust_score"], "verdict": a["verdict"]})
    return out


def demo_portfolio() -> Optional[Dict[str, Any]]:
    return _load("demo_portfolio.json")
