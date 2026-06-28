"""Unit tests for deterministic audit logic (no Anakin/LLM calls)."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services import audit_checks as ac
from services import anakin_budget_service as budget


def test_allocation_diff_delta():
    cur = [{"name": "Financials", "weight": 33.5}, {"name": "IT", "weight": 9.8}]
    prev = [{"name": "Financials", "weight": 28.0}, {"name": "IT", "weight": 11.5}]
    diff = {d["name"]: d for d in ac.build_allocation_diff(cur, prev)}
    assert diff["Financials"]["delta_percentage_points"] == 5.5
    assert diff["IT"]["delta_percentage_points"] == -1.7


def test_manager_said_vs_did_mismatch():
    claims = [{"asset_or_sector": "Financials", "direction": "underweight",
               "quoted_text": "underweight financials", "normalized_claim": "x", "confidence": 0.8}]
    diff = ac.build_allocation_diff([{"name": "Financials", "weight": 34.0}],
                                    [{"name": "Financials", "weight": 28.0}])
    res = ac.check_manager_said_vs_did(claims, diff)
    assert res["status"] in ("fail", "warning")
    assert res["score"] < 75


def test_manager_said_vs_did_consistent():
    claims = [{"asset_or_sector": "Consumer", "direction": "increase",
               "quoted_text": "adding consumer", "normalized_claim": "x", "confidence": 0.8}]
    diff = ac.build_allocation_diff([{"name": "Consumer", "weight": 16.0}],
                                    [{"name": "Consumer", "weight": 13.0}])
    res = ac.check_manager_said_vs_did(claims, diff)
    assert res["status"] == "pass"


def test_manager_said_vs_did_insufficient():
    res = ac.check_manager_said_vs_did([], [])
    assert res["status"] == "insufficient_data"


def test_style_drift_breach():
    mandate = {"min_large": 0, "min_largecap_pct": 80}
    holdings = [{"name": "A", "weight": 76, "market_cap_segment": "large"},
                {"name": "B", "weight": 24, "market_cap_segment": "mid"}]
    res = ac.check_style_drift({"min_largecap_pct": 80}, holdings)
    assert res["status"] in ("warning", "fail")


def test_manager_tenure_recent():
    res = ac.check_manager_tenure({"manager_start_date": "2026-01-01",
                                   "advertised_return_periods": ["5Y"]})
    assert res["status"] in ("warning", "pass")
    assert "tenure_months" in res


def test_manager_tenure_insufficient():
    res = ac.check_manager_tenure({})
    assert res["status"] == "insufficient_data"


def test_hidden_churn():
    cur = [{"name": "A", "weight": 50}, {"name": "B", "weight": 50}]
    prev = [{"name": "A", "weight": 50}, {"name": "C", "weight": 50}]
    res = ac.check_hidden_churn(cur, prev, published_turnover_pct=29)
    assert res["status"] == "pass"
    assert res["annualized_observed_churn_pct"] > 0


def test_nfo_clone():
    nfo = {"category": "Large Cap", "benchmark": "Nifty 50", "market_cap_mandate": "large",
           "sector_or_theme": "diversified", "structure": "active"}
    universe = [{"fund_name": "X", "category": "Large Cap", "benchmark": "Nifty 50",
                 "market_cap_mandate": "large", "sector_or_theme": "diversified", "structure": "active"}]
    res = ac.check_nfo_clone(nfo, universe)
    assert res["status"] in ("pass", "warning")
    assert res["closest"]


def test_trust_score_redistribution():
    checks = [
        {"check_id": "manager_said_vs_did", "status": "fail", "score": 33},
        {"check_id": "style_drift", "status": "warning", "score": 60},
        {"check_id": "manager_tenure", "status": "pass", "score": 85},
        {"check_id": "skin_in_game", "status": "insufficient_data", "score": 0},
    ]
    score, verdict = ac.compute_trust_score(checks)
    assert 0 <= score <= 100
    assert verdict in ("TRUSTED", "MONITOR", "REVIEW", "HIGH CONCERN")


def test_verdict_bands():
    assert ac.verdict_for_score(90) == "TRUSTED"
    assert ac.verdict_for_score(70) == "MONITOR"
    assert ac.verdict_for_score(50) == "REVIEW"
    assert ac.verdict_for_score(10) == "HIGH CONCERN"


def test_cache_key_normalization():
    k1 = budget.cache_key("https://Example.com/a/")
    k2 = budget.cache_key("https://example.com/a")
    assert k1 == k2


def test_budget_enforcement():
    from config import settings
    over = settings.ANAKIN_MAX_CREDITS_PER_AUDIT + 1
    try:
        budget.check_budget(over)
        assert False, "expected BudgetError"
    except budget.BudgetError:
        pass
