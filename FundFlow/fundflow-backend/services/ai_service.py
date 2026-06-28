import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict
import statistics

logger = logging.getLogger(__name__)

# "gemini-1.5-flash" was retired; the -latest alias tracks the current stable Flash model.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

AI_PROMPT_TEMPLATE = """You are FundFlow AI — an expert mutual fund analyst for Indian retail investors.

Analyze this mutual fund and return a strict JSON response.

Fund Details:
- Name: {fund_name}
- Category: {category}
- Scheme Code: {scheme_code}
- Units Held: {units}
- Buy NAV: {buy_nav}
- Current NAV: {current_nav}
- Current Value: ₹{current_value:.2f}
- Gain/Loss: ₹{gain_loss:.2f} ({gain_loss_pct:.2f}%)
- 1-Year Return: {one_year_return}%
- 30-Day Volatility (std dev): {volatility}%

Recent NAV trend (last 10 data points, most recent first):
{nav_trend}

Return ONLY valid JSON with this exact structure:
{{
  "verdict": "HOLD",
  "risk_level": "MODERATE",
  "risk_explanation": "...",
  "performance_summary": "...",
  "recommendation": "...",
  "key_signals": ["signal 1", "signal 2", "signal 3"],
  "best_for": "..."
}}

verdict must be one of: HOLD, ADD, EXIT, WATCH
risk_level must be one of: LOW, MODERATE, HIGH
All text fields should be in simple English (Hinglish is fine for recommendation).
Keep each field under 100 characters except recommendation (max 200 chars).
"""


REPORT_PROMPT_TEMPLATE = """You are FundFlow AI — a senior mutual fund research analyst writing a detailed report \
for an Indian retail investor. Write a clear, well-structured fund research report in plain text \
(no markdown symbols like #, *, or **; use simple section headings in ALL CAPS followed by a colon, \
and plain paragraphs / hyphen bullet points).

Fund Details:
- Name: {fund_name}
- Category: {category}
- Scheme Code: {scheme_code}
- Units Held: {units}
- Buy NAV: {buy_nav}
- Current NAV: {current_nav}
- Invested Amount: Rs. {invested_amount:.2f}
- Current Value: Rs. {current_value:.2f}
- Gain/Loss: Rs. {gain_loss:.2f} ({gain_loss_pct:.2f}%)
- 1-Year Return: {one_year_return}%
- 30-Day Volatility (std dev): {volatility}%

Quick AI Verdict (already computed):
- Verdict: {verdict}
- Risk Level: {risk_level}
- Risk Explanation: {risk_explanation}
- Performance Summary: {performance_summary}
- Recommendation: {recommendation}
- Best For: {best_for}

Recent NAV trend (last 10 data points, most recent first):
{nav_trend}

Write the report with EXACTLY these sections, in this order, each as an ALL CAPS heading on its own line \
followed by 1-3 paragraphs (or bullet points where useful):

FUND OVERVIEW
- Briefly describe the fund, its category, and what kind of investor it suits, based on the details above.

PERFORMANCE ANALYSIS
- Discuss the 1-year return, 30-day volatility, and the recent NAV trend. Explain what these numbers mean \
for the investor in simple terms.

RISK PROFILE
- State the risk level and explain the reasoning in more depth than the short verdict above.

PORTFOLIO FIT & RECOMMENDATION
- Give a clear verdict (HOLD/ADD/EXIT/WATCH) with detailed reasoning on whether this fund fits a typical \
retail investor's portfolio, considering the gain/loss position.

OUTLOOK & KEY CONSIDERATIONS
- Discuss the near-term outlook and 3-5 key things the investor should watch out for.

DISCLAIMER
- Add this exact line: "This is AI-generated analysis, not financial advice. Consult a SEBI-registered \
financial advisor."

Keep the total report between 400 and 700 words. Do not use markdown formatting symbols.
"""


def _calculate_one_year_return(nav_history: List[Dict]) -> Optional[float]:
    if len(nav_history) < 2:
        return None
    current = nav_history[0]["nav"]
    one_year_ago = nav_history[min(len(nav_history) - 1, 365)]["nav"] if len(nav_history) >= 365 else nav_history[-1]["nav"]
    if one_year_ago == 0:
        return None
    return round(((current - one_year_ago) / one_year_ago) * 100, 2)


def _calculate_volatility(nav_history: List[Dict], days: int = 30) -> Optional[float]:
    if len(nav_history) < days + 1:
        return None
    recent = nav_history[:days + 1]
    daily_returns = []
    for i in range(len(recent) - 1):
        if recent[i + 1]["nav"] != 0:
            ret = (recent[i]["nav"] - recent[i + 1]["nav"]) / recent[i + 1]["nav"] * 100
            daily_returns.append(ret)
    if len(daily_returns) < 2:
        return None
    return round(statistics.stdev(daily_returns), 4)


async def analyze_fund(
    scheme_code: str,
    fund_name: str,
    category: str,
    units: float,
    buy_nav: float,
    current_nav: float,
    nav_history: List[Dict],
) -> Dict:
    current_value = units * current_nav
    invested = units * buy_nav
    gain_loss = current_value - invested
    gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0

    one_year_return = _calculate_one_year_return(nav_history)
    volatility = _calculate_volatility(nav_history)
    nav_trend = "\n".join([f"{item['date']}: {item['nav']}" for item in nav_history[:10]])

    prompt = AI_PROMPT_TEMPLATE.format(
        fund_name=fund_name,
        category=category or "Unknown",
        scheme_code=scheme_code,
        units=units,
        buy_nav=buy_nav,
        current_nav=current_nav,
        current_value=current_value,
        gain_loss=gain_loss,
        gain_loss_pct=gain_loss_pct,
        one_year_return=one_year_return or "N/A",
        volatility=volatility or "N/A",
        nav_trend=nav_trend,
    )

    ai_result = await _call_groq(prompt) or await _call_gemini(prompt)

    if not ai_result:
        ai_result = {
            "verdict": "WATCH",
            "risk_level": "MODERATE",
            "risk_explanation": "Unable to analyze at this time.",
            "performance_summary": "Analysis unavailable.",
            "recommendation": "Please try again later.",
            "key_signals": ["Data unavailable", "Try refreshing NAV", "Check back soon"],
            "best_for": "General investors",
        }

    return {
        "metrics": {
            "current_nav": current_nav,
            "buy_nav": buy_nav,
            "units": units,
            "invested_amount": round(invested, 2),
            "current_value": round(current_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
            "one_year_return": one_year_return,
            "volatility_30d": volatility,
        },
        "ai_analysis": ai_result,
    }


async def _call_groq(prompt: str) -> Optional[Dict]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        logger.warning(f"Groq call failed: {e}")
    return None


async def _call_gemini(prompt: str) -> Optional[Dict]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = response.text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        logger.warning(f"Gemini call failed: {e}")
    return None


async def _call_gemini_text(prompt: str) -> Optional[str]:
    """Call Gemini 1.5 Flash and return the raw text response (no JSON parsing)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text or None
    except Exception as e:
        logger.warning(f"Gemini report generation failed: {e}")
    return None


def _fallback_report_text(
    scheme_code: str,
    fund_name: str,
    category: str,
    units: float,
    buy_nav: float,
    metrics: Dict,
    ai_analysis: Dict,
) -> str:
    """Build a plain-text report from already-computed metrics/ai_analysis when Gemini is unavailable."""
    one_year_return = metrics.get("one_year_return")
    volatility = metrics.get("volatility_30d")
    key_signals = ai_analysis.get("key_signals") or []
    signals_text = "\n".join(f"- {s}" for s in key_signals) if key_signals else "- No additional signals available."

    return f"""FUND OVERVIEW
{fund_name} (Scheme Code: {scheme_code}) is a {category or "mutual fund"}. You currently hold \
{units} units bought at an average NAV of Rs. {buy_nav:.2f}, with a current NAV of Rs. {metrics.get("current_nav", 0):.2f}.

PERFORMANCE ANALYSIS
1-Year Return: {one_year_return if one_year_return is not None else "N/A"}%
30-Day Volatility (std dev): {volatility if volatility is not None else "N/A"}%
{ai_analysis.get("performance_summary", "Performance summary unavailable.")}

RISK PROFILE
Risk Level: {ai_analysis.get("risk_level", "MODERATE")}
{ai_analysis.get("risk_explanation", "Risk explanation unavailable.")}

PORTFOLIO FIT & RECOMMENDATION
Verdict: {ai_analysis.get("verdict", "WATCH")}
{ai_analysis.get("recommendation", "Recommendation unavailable.")}
Best suited for: {ai_analysis.get("best_for", "General investors")}

OUTLOOK & KEY CONSIDERATIONS
{signals_text}

DISCLAIMER
This is AI-generated analysis, not financial advice. Consult a SEBI-registered financial advisor.
"""


def _parse_report_sections(report_text: str) -> List[Dict[str, str]]:
    """Split a plain-text report into (heading, body) sections based on ALL CAPS headings."""
    known_headings = [
        "FUND OVERVIEW",
        "PERFORMANCE ANALYSIS",
        "RISK PROFILE",
        "PORTFOLIO FIT & RECOMMENDATION",
        "PORTFOLIO FIT AND RECOMMENDATION",
        "OUTLOOK & KEY CONSIDERATIONS",
        "OUTLOOK AND KEY CONSIDERATIONS",
        "DISCLAIMER",
    ]
    lines = report_text.splitlines()
    sections: List[Dict[str, str]] = []
    current_heading = None
    current_body: List[str] = []

    def flush():
        if current_heading is not None:
            body = "\n".join(current_body).strip()
            if body:
                sections.append({"heading": current_heading, "body": body})

    for line in lines:
        stripped = line.strip().strip(":").strip()
        normalized = stripped.upper()
        if normalized in known_headings and len(stripped) < 60:
            flush()
            current_heading = stripped.upper()
            current_body = []
        else:
            current_body.append(line)
    flush()

    if not sections:
        # Couldn't detect headings — return the whole text as one section.
        sections = [{"heading": "FUND ANALYSIS REPORT", "body": report_text.strip()}]

    return sections


async def generate_fund_report_pdf(
    scheme_code: str,
    fund_name: str,
    category: Optional[str],
    units: float,
    buy_nav: float,
    metrics: Dict,
    ai_analysis: Dict,
    nav_history: Optional[List[Dict]] = None,
) -> bytes:
    """Generate a detailed AI fund research report and render it as a PDF (returns PDF bytes)."""
    nav_history = nav_history or []
    nav_history_trend = "\n".join([f"{item['date']}: {item['nav']}" for item in nav_history[:10]])

    prompt = REPORT_PROMPT_TEMPLATE.format(
        fund_name=fund_name,
        category=category or "Unknown",
        scheme_code=scheme_code,
        units=units,
        buy_nav=buy_nav,
        current_nav=metrics.get("current_nav", buy_nav),
        invested_amount=metrics.get("invested_amount", 0.0),
        current_value=metrics.get("current_value", 0.0),
        gain_loss=metrics.get("gain_loss", 0.0),
        gain_loss_pct=metrics.get("gain_loss_pct", 0.0),
        one_year_return=metrics.get("one_year_return") if metrics.get("one_year_return") is not None else "N/A",
        volatility=metrics.get("volatility_30d") if metrics.get("volatility_30d") is not None else "N/A",
        verdict=ai_analysis.get("verdict", "WATCH"),
        risk_level=ai_analysis.get("risk_level", "MODERATE"),
        risk_explanation=ai_analysis.get("risk_explanation", "N/A"),
        performance_summary=ai_analysis.get("performance_summary", "N/A"),
        recommendation=ai_analysis.get("recommendation", "N/A"),
        best_for=ai_analysis.get("best_for", "General investors"),
        nav_trend=nav_history_trend or "Not available.",
    )

    report_text = await _call_gemini_text(prompt)
    if not report_text:
        report_text = _fallback_report_text(
            scheme_code=scheme_code,
            fund_name=fund_name,
            category=category or "Unknown",
            units=units,
            buy_nav=buy_nav,
            metrics=metrics,
            ai_analysis=ai_analysis,
        )

    sections = _parse_report_sections(report_text)
    return _build_report_pdf(scheme_code, fund_name, category, sections)


def _build_report_pdf(
    scheme_code: str,
    fund_name: str,
    category: Optional[str],
    sections: List[Dict[str, str]],
) -> bytes:
    from fpdf import FPDF

    ACCENT_COLOR = (107, 78, 255)  # #6B4EFF
    DARK_TEXT = (33, 33, 33)
    GREY_TEXT = (110, 110, 110)

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header — FundFlow branding
    pdf.set_text_color(*ACCENT_COLOR)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "FundFlow", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY_TEXT)
    pdf.cell(0, 6, "AI-Generated Fund Research Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Divider line
    pdf.set_draw_color(*ACCENT_COLOR)
    pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    # Fund title block
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, _sanitize(fund_name), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY_TEXT)
    pdf.cell(0, 6, f"Scheme Code: {scheme_code}", new_x="LMARGIN", new_y="NEXT")
    if category:
        pdf.cell(0, 6, f"Category: {_sanitize(category)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated on: {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Report sections
    for section in sections:
        heading = section["heading"]
        body = section["body"]

        # Section heading
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*ACCENT_COLOR)
        pdf.ln(2)
        pdf.multi_cell(0, 8, _sanitize(heading), new_x="LMARGIN", new_y="NEXT")

        # Section body
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(*DARK_TEXT)
        for paragraph in body.split("\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                pdf.ln(2)
                continue
            pdf.multi_cell(0, 6, _sanitize(paragraph), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # Footer
    pdf.ln(6)
    pdf.set_draw_color(*ACCENT_COLOR)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY_TEXT)
    pdf.multi_cell(
        0,
        5,
        "Powered by Mediflow Nexus\n"
        "This is AI-generated analysis, not financial advice. Consult a SEBI-registered financial advisor.",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    output = pdf.output()
    return bytes(output)


def _sanitize(text: str) -> str:
    """Replace characters not supported by the default PDF Helvetica font (latin-1) to avoid render errors."""
    if text is None:
        return ""
    replacements = {
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "…": "...", "₹": "Rs. ",
        "•": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.encode("latin-1", "replace").decode("latin-1")
    # Break tokens longer than a printable line (e.g. markdown table rules) so fpdf can wrap them.
    words = text.split(" ")
    words = [w if len(w) <= 90 else " ".join(w[i:i + 90] for i in range(0, len(w), 90)) for w in words]
    return " ".join(words)


async def compare_funds(scheme_data_list: List[Dict]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Comparison service temporarily unavailable."
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        funds_text = "\n".join([
            f"- {d['scheme_name']} (Code: {d['scheme_code']}): NAV {d['nav']}, Category: {d['category']}"
            for d in scheme_data_list
        ])
        prompt = f"""Compare these Indian mutual funds for an Indian retail investor:
{funds_text}

Give a concise comparison covering: performance, risk, category, who should invest. Under 200 words."""
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI compare failed: {e}")
        return "Fund comparison temporarily unavailable."


async def generate_voice_script(portfolio_summary: Dict) -> str:
    total_value = portfolio_summary.get("total_current_value", 0)
    total_gain_pct = portfolio_summary.get("total_gain_loss_pct", 0)
    direction = "up" if total_gain_pct >= 0 else "down"
    holdings = portfolio_summary.get("holdings", [])
    best_fund = max(holdings, key=lambda x: x.get("gain_loss_pct", 0), default={}) if holdings else {}
    best_name = best_fund.get("fund_name", "")[:20] if best_fund else ""

    value_str = f"{total_value:,.0f}"
    # Format as Indian number (lakh/crore)
    if total_value >= 10_000_000:
        value_str = f"{total_value / 10_000_000:.1f} crore"
    elif total_value >= 100_000:
        value_str = f"{total_value / 100_000:.1f} lakh"
    else:
        value_str = f"{total_value:,.0f} rupees"

    script = (
        f"Good morning. Your FundFlow portfolio is {direction} {abs(total_gain_pct):.1f} percent today. "
        f"Total value is {value_str}. "
    )
    if best_name:
        best_pct = best_fund.get("gain_loss_pct", 0)
        script += f"{best_name} is your top performer at {'plus' if best_pct >= 0 else 'minus'} {abs(best_pct):.1f} percent. "
    script += "Have a great investing day!"
    return script[:300]
