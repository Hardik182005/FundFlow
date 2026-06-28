# Audit Methodology

All numeric calculations happen in Python (`services/audit_checks.py`). The LLM only extracts
quoted values from documents (`services/audit_extraction_service.py`); it never computes deltas.

## Checks

- **Manager Said vs Did** (weight 35) — match each manager portfolio-action statement to the
  observed sector move: `delta = current − previous`; increase ≥ +1.0 pp, decrease ≤ −1.0 pp
  (configurable). Market opinions with no action promise are not counted as broken. Score =
  consistent / evaluated × 100. Language: "statement–portfolio mismatch" / "execution gap".
- **Style Drift** (25) — sum holding weights per market-cap segment vs the mandate floor. Labelled
  "potential style drift" unless evidence clearly supports a breach. No claim of legal consent.
- **Manager Continuity** (15) — tenure_months from disclosed start date vs advertised return
  periods. No invented percentile ranks.
- **NFO Clone Detector** (15, when an NFO doc exists) — deterministic weighted similarity
  (category 20 / benchmark 20 / mandate 25 / sector 20 / style 10 / fee 5) against a curated
  universe. Shows the size of that universe explicitly.
- **Skin in the Game** (5) — manager investment if disclosed; ₹0 is not misconduct.
- **Churn Transparency** (5) — `monthly = 1 − Σ min(cur,prev)`, annualised & capped. Explicitly
  *not* the official SEBI turnover formula.

## Trust score & verdict

Weighted average of present checks; weights of `insufficient_data` checks are redistributed
proportionally. Bands: 80–100 TRUSTED, 65–79 MONITOR, 45–64 REVIEW, 0–44 HIGH CONCERN. Optional
action label (HOLD/WATCH/REVIEW/REASSESS) is shown, never as certainty.

Missing inputs → `insufficient_data` (never a fabricated pass/fail). Every check exposes its
`methodology` string in a "How this was calculated" panel.
