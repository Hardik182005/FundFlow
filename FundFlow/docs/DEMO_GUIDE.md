# FundFlow — 3-Minute Demo Script

**Setup:** `FUNDFLOW_DEMO_MODE=true`. Backend on :8080, frontend on :3000. A cached demo audit
(`aud_demo_hdfc_midcap`) and a 3-fund demo portfolio ship under `fixtures/demo/`.

1. **Landing (0:00–0:30)** — Open `/`. Tagline *"Track your funds. Trust your funds."* Point at
   the animated **pipeline**: Claim Layer (Anakin Scraper) → Reality Layer (Anakin Wire) →
   Reasoning Layer (Gemini + deterministic) → Voice Layer (ElevenLabs). Click **Open FundFlow**.

2. **Audit a fund (0:30–1:15)** — Go to **Audit Funds**. Pick *HDFC Mid-Cap Opportunities*.
   Show the **Estimated Anakin usage** card (fresh credits / cached / Wire available). Click
   **Run Audit** — narrate the real pipeline stages. (Live mode performs a real Anakin scrape +
   one Wire action; demo mode opens the cached audit instantly.)

3. **Audit result (1:15–2:15)** — Trust Score + verdict badge. Open **Manager Said vs Did**:
   the table shows *"underweight financials"* vs financials actually rising 28% → 33.5%
   (**Mismatch**). Flip tabs: **Allocation Diff**, **Evidence** (source, reporting period,
   Anakin job ID, cache status, excerpt), **Methodology** ("How this was calculated").

4. **Voice + chat (2:15–2:45)** — Open the **FundFlow Orb**. Click **Read aloud** on the result
   (ElevenLabs narration ≤140 words). Ask the orb *"Why did this fund receive a warning?"* — it
   answers grounded in the saved audit evidence, no new Anakin call.

5. **Anakin usage (2:45–3:00)** — **Anakin Usage** page: configured budget, locally-tracked
   credits, cache-hit rate, discovered Wire actions, last 20 calls. Close with the disclaimer.

**Talking point:** every conclusion is evidence-linked; missing data is shown as
*Insufficient evidence*, never converted into a pass or fail.
