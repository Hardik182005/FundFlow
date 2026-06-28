import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
