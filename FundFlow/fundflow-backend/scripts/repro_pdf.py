"""Reproduce the /api/analysis/fund/report 500: fetch real Gemini report text and build the PDF locally."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from services.ai_service import _call_gemini_text, _parse_report_sections, _build_report_pdf, REPORT_PROMPT_TEMPLATE


async def main():
    prompt = REPORT_PROMPT_TEMPLATE.format(
        fund_name="SBI Bluechip Fund Regular Growth",
        category="Equity Scheme - Large Cap Fund",
        scheme_code="119598",
        units=100,
        buy_nav=70.5,
        current_nav=100.565,
        invested_amount=7050.0,
        current_value=10056.5,
        gain_loss=3006.5,
        gain_loss_pct=42.65,
        one_year_return=3.24,
        volatility=0.7517,
        verdict="HOLD",
        risk_level="MODERATE",
        risk_explanation="30-day volatility is 0.75%",
        performance_summary="42% gain",
        recommendation="Hold for long term",
        best_for="Long term",
        nav_trend="09-06-2026: 100.565",
    )
    text = await _call_gemini_text(prompt)
    print("=== GEMINI RETURNED:", "None (fallback path)" if not text else f"{len(text)} chars")
    if text:
        with open("scripts/gemini_report_sample.txt", "w", encoding="utf-8") as f:
            f.write(text)
    sections = _parse_report_sections(text or "FUND OVERVIEW\nfallback")
    try:
        pdf = _build_report_pdf("119598", "SBI Bluechip Fund Regular Growth", "Equity Scheme - Large Cap Fund", sections)
        print(f"=== PDF OK: {len(pdf)} bytes")
    except Exception as e:
        print(f"=== PDF CRASH: {type(e).__name__}: {e}")
        # find the offending paragraph
        from services.ai_service import _sanitize
        for s in sections:
            for p in s["body"].split("\n"):
                p = p.strip()
                if p and max((len(tok) for tok in _sanitize(p).split(" ")), default=0) > 60:
                    print("LONG TOKEN PARA:", repr(p[:120]))


asyncio.run(main())
