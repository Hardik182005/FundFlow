import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from services.ai_service import _fallback_report_text, _parse_report_sections, _sanitize
from fpdf import FPDF

text = _fallback_report_text(
    "119598", "SBI Bluechip Fund Regular Growth", "Equity Scheme - Large Cap Fund", 100, 70.5,
    {"current_nav": 100.565, "one_year_return": 3.24, "volatility_30d": 0.7517},
    {"verdict": "HOLD", "risk_level": "MODERATE", "risk_explanation": "30-day volatility is 0.75%",
     "performance_summary": "42% gain", "recommendation": "Hold for long term",
     "key_signals": ["High gain", "Low volatility", "Stable NAV"], "best_for": "Long term"})
sections = _parse_report_sections(text)
pdf = FPDF(format="A4")
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()
pdf.set_font("Helvetica", "", 10.5)
for s in sections:
    for p in s["body"].split("\n"):
        p = p.strip()
        if not p:
            continue
        try:
            pdf.multi_cell(0, 6, _sanitize(p))
        except Exception as e:
            print("CRASH on:", repr(p))
            print("x=", pdf.x, "l_margin=", pdf.l_margin, "r_margin=", pdf.r_margin, "w=", pdf.w, "epw=", pdf.epw)
            raise
print("ALL OK")
