"""Verify the FundFlow ElevenLabs ConvAI agent exists and measure TTS latency."""
import os
import sys
import json
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = "agent_3001ktsbqg4me1bbgfh3cbrfev2t"


def req(method, path, payload=None, raw=False):
    r = urllib.request.Request(f"https://api.elevenlabs.io{path}",
                               data=json.dumps(payload).encode() if payload else None, method=method)
    r.add_header("xi-api-key", API_KEY)
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as resp:
        body = resp.read()
        return resp.status, body if raw else json.loads(body)


# 1. Agent exists + config
status, agent = req("GET", f"/v1/convai/agents/{AGENT_ID}")
cfg = agent.get("conversation_config", {})
print(f"agent: HTTP {status}, name={agent.get('name')}")
print(f"  first_message: {cfg.get('agent', {}).get('first_message', '')[:60]}...")
print(f"  voice_id: {cfg.get('tts', {}).get('voice_id')}, model: {cfg.get('tts', {}).get('model_id')}")

# 2. Signed conversation URL (what the widget requests to start a session)
t0 = time.time()
status2, link = req("GET", f"/v1/convai/conversation/get-signed-url?agent_id={AGENT_ID}")
print(f"signed conversation URL: HTTP {status2} in {time.time()-t0:.2f}s (session can start)")

# 3. TTS latency (the same call the backend /api/voice/tts makes)
t0 = time.time()
status3, audio = req("POST", "/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM?output_format=mp3_44100_128",
                     {"text": "Your portfolio is up one point two percent today.", "model_id": "eleven_turbo_v2_5"}, raw=True)
print(f"TTS: HTTP {status3}, {len(audio)} bytes in {time.time()-t0:.2f}s")
