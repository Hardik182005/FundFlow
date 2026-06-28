"""
Create (or reuse) the FundFlow ElevenLabs Conversational AI agent.

Reads ELEVENLABS_API_KEY from fundflow-backend/.env, creates a ConvAI agent
configured for FundFlow, and prints the resulting agent_id. The agent_id is NOT
a secret (it is used client-side as NEXT_PUBLIC_ELEVENLABS_AGENT_ID).

Usage:  python scripts/create_voice_agent.py
"""
import os
import sys
import json
import urllib.request
import urllib.error

from dotenv import load_dotenv

# Load .env from the backend root (one level up from scripts/)
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BACKEND_ROOT, ".env"))

API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE = "https://api.elevenlabs.io"

# "Rachel" — a clear, friendly default voice
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

SYSTEM_PROMPT = (
    "You are FundFlow Assistant, a warm and friendly voice assistant for Indian retail "
    "mutual fund investors using the FundFlow app. You help users understand their mutual "
    "fund portfolio: current value, total gains and losses, individual fund NAV, and the "
    "AI verdicts FundFlow assigns to each fund (HOLD, ADD, EXIT, or WATCH). "
    "Speak in simple, clear English; light Hinglish is welcome for warmth. "
    "Use Indian number conventions (rupees, lakh, crore). Keep every answer short and "
    "conversational, ideally two or three sentences. FundFlow tracks funds using official "
    "AMFI India NAV data. If a user asks for an exact live figure you do not have in context, "
    "gently suggest they check the precise number on their FundFlow dashboard. "
    "Never present financial advice as a guarantee; for major decisions, remind users to "
    "consult a SEBI-registered financial advisor. Be encouraging, positive, and concise."
)

FIRST_MESSAGE = (
    "Hi! I'm your FundFlow assistant. Ask me anything about your mutual fund portfolio - "
    "how it's doing today, which fund is your top performer, or whether you should hold or add."
)


def _request(method, path, payload=None):
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("xi-api-key", API_KEY)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def main():
    if not API_KEY:
        print("ERROR: ELEVENLABS_API_KEY is not set in fundflow-backend/.env")
        sys.exit(2)

    # 1) Verify the key + ConvAI access by listing existing agents.
    status, body = _request("GET", "/v1/convai/agents?page_size=30")
    if status != 200:
        print(f"ERROR: Could not access ElevenLabs Conversational AI (HTTP {status}).")
        print(f"Detail: {body}")
        print("Note: Conversational AI may require a paid ElevenLabs plan.")
        sys.exit(1)

    # Reuse an existing FundFlow agent if one already exists (idempotent).
    existing = body.get("agents", []) if isinstance(body, dict) else []
    for a in existing:
        if (a.get("name") or "").strip().lower() == "fundflow assistant":
            print(f"AGENT_ID={a.get('agent_id')}")
            print("(reused existing 'FundFlow Assistant' agent)")
            return

    # 2) Create the agent.
    payload = {
        "name": "FundFlow Assistant",
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": SYSTEM_PROMPT},
                "first_message": FIRST_MESSAGE,
                "language": "en",
            },
            "tts": {"voice_id": VOICE_ID},
        },
    }
    status, body = _request("POST", "/v1/convai/agents/create", payload)
    if status not in (200, 201) or not isinstance(body, dict):
        print(f"ERROR: Agent creation failed (HTTP {status}).")
        print(f"Detail: {body}")
        sys.exit(1)

    agent_id = body.get("agent_id")
    if not agent_id:
        print(f"ERROR: No agent_id in response: {body}")
        sys.exit(1)

    print(f"AGENT_ID={agent_id}")
    print("(created new 'FundFlow Assistant' agent)")


if __name__ == "__main__":
    main()
