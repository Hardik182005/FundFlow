"""Generate the FundFlow Audit PDF from structured audit data (not a screenshot)."""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger("fundflow.report")


def _clean(text: str) -> str:
    if text is None:
        return ""
    # fpdf core fonts are latin-1; replace common unicode
    repl = {"’": "'", "‘": "'", "“": '"', "”": '"',
            "–": "-", "—": "-", "₹": "Rs ", "→": "->", "•": "-"}
    for k, v in repl.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


def build_audit_pdf(audit: Dict[str, Any]) -> bytes:
    from fpdf import FPDF, XPos, YPos
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "FundFlow Audit Report", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 6, _clean("Track your funds. Trust your funds."), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(pdf.epw, 7, _clean(audit.get("fund_name", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _clean(f"Scheme code: {audit.get('scheme_code')}  |  Generated: {audit.get('generated_at','')[:19]}"), ln=True)
    if audit.get("is_demo"):
        pdf.set_text_color(180, 120, 0)
        pdf.cell(0, 6, "Demo audit generated from cached source documents.", ln=True)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Trust score box
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _clean(f"Trust Score: {audit.get('trust_score')}/100   Verdict: {audit.get('verdict')}"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(pdf.epw, 6, _clean(audit.get("verdict_explanation", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # Checks
    for c in audit.get("checks", []):
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(pdf.epw, 6, _clean(f"{c['name']} — {c['status'].upper()} ({c['score']})"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(pdf.epw, 5, _clean(c.get("summary", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for f in c.get("findings", []):
            pdf.multi_cell(pdf.epw, 5, _clean(f"  - {f}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(pdf.epw, 5, _clean(f"  Methodology: {c.get('methodology','')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    # Evidence
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Evidence", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for e in audit.get("evidence", []):
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(pdf.epw, 5, _clean(f"{e.get('source_type')}: {e.get('title')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(90, 90, 110)
        meta = f"{e.get('url')}  | period: {e.get('reporting_period')} | Anakin job: {e.get('anakin_job_id')} | {'cached' if e.get('cached') else 'fresh'}"
        pdf.multi_cell(pdf.epw, 4, _clean(meta), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        if e.get("excerpt"):
            pdf.multi_cell(pdf.epw, 4, _clean(f"\"{e['excerpt']}\""), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    # Limitations + disclaimer
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Limitations", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for l in audit.get("limitations", []):
        pdf.multi_cell(pdf.epw, 5, _clean(f"- {l}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(pdf.epw, 4, _clean(audit.get("disclaimer", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
