<div align="center">

# FundFlow — Track your funds. Trust your funds.

**AI-powered mutual-fund manager-accountability platform — powered by Anakin Universal Scraper + Wire.**

![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
<br/>
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=awslambda&logoColor=white)
![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white)
![CloudFront](https://img.shields.io/badge/CloudFront-8C4FFF?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon ECR](https://img.shields.io/badge/Amazon_ECR-FF9900?style=for-the-badge&logo=amazonecs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
<br/>
![Anakin](https://img.shields.io/badge/Anakin-Universal_Scraper_+_Wire-0B0D12?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice-000000?style=for-the-badge)
<br/>
![Build](https://img.shields.io/badge/build-passing-0E9F6E?style=for-the-badge)
![Tests](https://img.shields.io/badge/tests-13_passing-0E9F6E?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)
![PRs](https://img.shields.io/badge/PRs-welcome-0E9F6E?style=for-the-badge)

### 🔗 Live Demo
**App:** https://d2t54cdr6pa9af.cloudfront.net &nbsp;·&nbsp; **API:** https://wg6uesr84e.execute-api.eu-west-1.amazonaws.com

</div>

---

FundFlow is a mutual-fund product with two connected modules:

1. **FundFlow Portfolio** — the existing AMFI/NAV portfolio tracker (preserved).
2. **FundFlow Audit** — a new manager-accountability product built on **Anakin
   Universal Scraper + Wire**, Gemini extraction, deterministic Python scoring, and
   ElevenLabs voice.

> AI-assisted document & portfolio consistency audit — **not** investment advice.
> Verify source documents and consult a SEBI-registered investment adviser.

## Architecture

```
Claim Layer     →  Anakin Universal Scraper  (factsheets, commentary, SID, annual report → Markdown)
Reality Layer   →  Anakin Wire               (morningstar-in / NSE / BSE / ET structured data)
Reasoning Layer →  Gemini (Groq fallback) + deterministic Python scoring (all numbers in Python)
Voice Layer     →  ElevenLabs (audit narration + assistant)
```

The six audit checks: **Manager Said vs Did**, **Style Drift**, **Manager Continuity**,
**NFO Clone Detector**, **Skin in the Game**, **Churn Transparency** → combined into a
0–100 **Trust Score** (TRUSTED / MONITOR / REVIEW / HIGH CONCERN). Every conclusion links
to source evidence; missing data returns `insufficient_data` (never a fabricated pass/fail).

## Project layout

```
fundflow-backend/    FastAPI — routers/, services/, models/, config/, fixtures/demo/, tests/
fundflow-frontend/   Next.js 14 App Router (static export) — app/, components/, lib/
```

## Local run

Backend:
```bash
cd fundflow-backend
pip install -r requirements.txt
cp .env.example .env   # fill in keys (see below)
uvicorn main:app --reload --port 8080
```

Frontend:
```bash
cd fundflow-frontend
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:8080
npm run dev
```

## Required environment

Backend (`fundflow-backend/.env`): `ANAKIN_API_KEY` (free 500-credit key from the Anakin
dashboard), `GEMINI_API_KEY`, `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`.
See `.env.example` for the full list including the Anakin budget/cache and `WIRE_ACTION_*`
override variables. Persistence is **in-memory** — no database/Firebase is required.

Frontend: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` (only these are exposed to
the browser).

Without `ANAKIN_API_KEY` the app still runs fully in **demo mode** (`FUNDFLOW_DEMO_MODE=true`)
using cached fixtures under `fixtures/demo/`.

## Tests

```bash
cd fundflow-backend && python -m pytest tests/ -q     # 13 deterministic checks, Anakin mocked
cd fundflow-frontend && npm run build                 # static export, all routes
```

See `docs/` for Anakin integration, audit methodology, the 3-minute demo script, and deployment.
