"""ElevenLabs Text-to-Speech service.

Turns short text scripts into spoken MP3 audio. Used to give FundFlow a friendly
voice — e.g. narrating a fund's analysis when the user generates a report, or
reading out a portfolio summary in the voice assistant.

Only needs the `text_to_speech` permission on the ElevenLabs API key (NOT the
`convai_write` permission required by full Conversational AI agents).
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io"
# "Rachel" — a clear, friendly default voice. Override with ELEVENLABS_VOICE_ID.
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
DEFAULT_MODEL = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_turbo_v2_5")


async def synthesize_speech(text: str, voice_id: str | None = None) -> bytes | None:
    """Convert text to MP3 audio bytes via ElevenLabs TTS. Returns None on failure."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not set — cannot synthesize speech.")
        return None

    text = (text or "").strip()
    if not text:
        return None
    # Keep narrations short and snappy (and within reasonable TTS limits).
    text = text[:1200]

    voice = voice_id or DEFAULT_VOICE_ID
    url = f"{ELEVENLABS_BASE}/v1/text-to-speech/{voice}"
    payload = {
        "text": text,
        "model_id": DEFAULT_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.content
            logger.warning(
                "ElevenLabs TTS failed (HTTP %s): %s",
                resp.status_code,
                resp.text[:300],
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("ElevenLabs TTS request error: %s", e)
    return None


def build_fund_narration(fund_name: str, metrics: dict, ai_analysis: dict) -> str:
    """Compose a short, friendly spoken summary of a fund's analysis (<~120 words)."""
    gain_pct = metrics.get("gain_loss_pct", 0) or 0
    verdict = (ai_analysis.get("verdict") or "WATCH").upper()
    risk = (ai_analysis.get("risk_level") or "moderate").lower()

    direction = "up" if gain_pct >= 0 else "down"
    verdict_phrase = {
        "ADD": "our verdict is ADD — it looks like a good one to accumulate",
        "HOLD": "our verdict is HOLD — staying invested looks sensible",
        "EXIT": "our verdict is EXIT — you may want to review this position",
        "WATCH": "our verdict is WATCH — keep an eye on it for now",
    }.get(verdict, "keep an eye on it for now")

    # Trim very long fund names for a natural read.
    short_name = fund_name.split(" - ")[0][:60]

    return (
        f"Here is your FundFlow analysis for {short_name}. "
        f"This holding is currently {direction} {abs(gain_pct):.1f} percent. "
        f"It carries {risk} risk, and {verdict_phrase}. "
        f"{ai_analysis.get('recommendation', '')} "
        "You can read the full detailed report in the PDF. "
        "Remember, this is AI analysis, not financial advice."
    ).strip()
