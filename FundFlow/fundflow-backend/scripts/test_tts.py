"""Quick probe: does the ELEVENLABS_API_KEY have text-to-speech permission?"""
import os, json, urllib.request, urllib.error
from dotenv import load_dotenv

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE = "21m00Tcm4TlvDq8ikWAM"  # Rachel

req = urllib.request.Request(
    f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}",
    data=json.dumps({"text": "FundFlow voice test.", "model_id": "eleven_turbo_v2_5"}).encode(),
    method="POST",
)
req.add_header("xi-api-key", KEY)
req.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        audio = r.read()
        print(f"TTS_OK bytes={len(audio)} content_type={r.headers.get('Content-Type')}")
except urllib.error.HTTPError as e:
    print(f"TTS_FAIL http={e.code} detail={e.read().decode('utf-8','replace')[:300]}")
except Exception as e:
    print(f"TTS_FAIL other={e}")
