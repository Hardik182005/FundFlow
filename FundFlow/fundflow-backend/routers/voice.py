from fastapi import APIRouter, HTTPException, Response
from models.schemas import (
    VoiceSummaryRequest, VoiceSummaryResponse, TTSRequest, AnalysisFundRequest,
)
from services.store_service import get_portfolio
from services.amfi_service import get_latest_nav, get_nav_history
from services.ai_service import generate_voice_script, analyze_fund
from services.tts_service import synthesize_speech, build_fund_narration

router = APIRouter()


@router.post("/summary", response_model=VoiceSummaryResponse)
async def get_voice_summary(body: VoiceSummaryRequest):
    portfolio = await get_portfolio(body.user_id)
    if not portfolio:
        return VoiceSummaryResponse(
            script="Hi! I could not find your portfolio. Please add your mutual funds to get started."
        )

    holdings_raw = portfolio.get("holdings", [])
    total_invested = 0
    total_current = 0
    holding_summaries = []

    for h in holdings_raw:
        nav_data = await get_latest_nav(h["scheme_code"])
        if not nav_data:
            continue
        units = h["units"]
        buy_nav = h["buy_nav"]
        current_nav = nav_data["nav"]
        invested = units * buy_nav
        current_value = units * current_nav
        gain_loss = current_value - invested
        gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0
        total_invested += invested
        total_current += current_value
        holding_summaries.append({
            "fund_name": h.get("fund_name", nav_data.get("scheme_name", "")),
            "gain_loss_pct": round(gain_loss_pct, 2),
        })

    total_gain_loss = total_current - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0

    summary = {
        "total_current_value": round(total_current, 2),
        "total_gain_loss_pct": round(total_gain_loss_pct, 2),
        "holdings": holding_summaries,
    }
    script = await generate_voice_script(summary)
    return VoiceSummaryResponse(script=script)


@router.post("/tts")
async def text_to_speech(body: TTSRequest):
    """Convert arbitrary text into spoken MP3 audio (ElevenLabs TTS)."""
    audio = await synthesize_speech(body.text)
    if not audio:
        raise HTTPException(status_code=503, detail="Voice synthesis unavailable.")
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/audit-narration")
async def audit_narration(body: dict):
    """Narrate an audit verdict (<=140 words) as MP3 via ElevenLabs."""
    from services import fund_audit_service, demo_service, assistant_service
    audit_id = body.get("audit_id")
    audit = fund_audit_service.get_audit(audit_id) or demo_service.get_demo_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found.")
    script = assistant_service.build_audit_narration(audit)
    audio = await synthesize_speech(script)
    if not audio:
        # caller (frontend) falls back to browser speech synthesis
        return {"script": script, "audio_available": False}
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/fund-narration")
async def fund_narration(body: AnalysisFundRequest):
    """Analyze a fund and return a short spoken narration of the verdict as MP3."""
    nav_data = await get_latest_nav(body.scheme_code)
    if not nav_data:
        raise HTTPException(status_code=404, detail="NAV data not available.")
    nav_history = await get_nav_history(body.scheme_code, 365)
    result = await analyze_fund(
        scheme_code=body.scheme_code,
        fund_name=body.fund_name,
        category=body.category or nav_data.get("category", ""),
        units=body.units,
        buy_nav=body.buy_nav,
        current_nav=nav_data["nav"],
        nav_history=nav_history,
    )
    script = build_fund_narration(body.fund_name, result["metrics"], result["ai_analysis"])
    audio = await synthesize_speech(script)
    if not audio:
        raise HTTPException(status_code=503, detail="Voice synthesis unavailable.")
    return Response(content=audio, media_type="audio/mpeg")
