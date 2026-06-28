# Anakin Integration

All external web intelligence in FundFlow Audit goes through Anakin. AMFI/mfapi remain only
for the existing NAV pipeline. No direct scraping of AMC/Morningstar/NSE/BSE/news sites.

## Universal Scraper

`services/anakin_client.py` (`scrape_url`, `scrape_batch`):
```
POST /url-scraper            -> { jobId }
GET  /url-scraper/{jobId}    -> { status, markdown, json, ... }
```
Async polling with exponential backoff (2→3→5→8s). Browser mode is used only as a fallback
when a normal scrape returns < 200 chars. `generateJson` is **off** by default — we use Gemini
on the Markdown instead (cheaper, more controllable).

## Wire

```
GET  /wire/search ; GET /wire/catalog/{slug} ; POST /wire/task ; GET /wire/jobs/{jobId}
```
`services/wire_registry_service.py` maps logical purposes → concrete action IDs. Resolution
order: `WIRE_ACTION_*` env override → Firestore `wire_action_registry/{logical}` → seeded
`config/wire_actions_default.json`. **Action IDs are never invented** — they are discovered via
`POST /api/anakin/discover-wire-actions` (or seeded from a real discovery run).

### Real discovered actions (verified live)
| Logical | action_id | catalog | credits |
|---|---|---|---|
| fund_profile | `act_morningstar_in_mutual_fund_detail_ssr` | morningstar-in | 2 |
| fund_holdings | `act_morningstar_in_mutual_fund_portfolio_ssr` | morningstar-in | 2 |
| fund_manager_news / nfo_news | `et_mutual_funds` | economic_times | 1 |
| security_market_cap | `bse_quote` | bse | 2 |
| security_profile | `nse_52week_highlow` | nse_india | 1 |

Morningstar holdings render client-side, so the SSR portfolio action returns fund
profile/ISIN/rating (reality layer); allocation tables come from Universal Scraper + Gemini.

## Caching & credit control (`services/anakin_budget_service.py`)

- Cache by normalized URL + extraction version. Scraper Markdown reused 7 days; source
  discovery / Wire discovery 30 days; audit results 24h.
- Firestore ledger: `anakin_usage`, `anakin_budget/current`, `anakin_cache`,
  `wire_action_registry` (degrades to in-memory without Firestore).
- Per-audit limits: ≤4 fresh scrapes, ≤1 Wire action, 0 search calls normally.
- Pre-flight estimate + `check_budget()`; returns 402 / friendly error if the budget would be
  exceeded. Idempotency key prevents double-click duplicate paid calls.
- `GET /api/anakin/usage` → "Locally tracked Anakin usage" (NOT Anakin's official balance).

## Adding a new Wire action
Run discovery, or set `WIRE_ACTION_*` env / write `wire_action_registry/{logical}` in Firestore.

## Adding a new AMC / fund source
Add to `config/fund_source_registry.json` or via Settings → Fund Sources
(`PUT /api/sources/funds/{scheme_code}`). Validate URLs with `POST /api/sources/validate`
(one low-cost scrape, cached). Never invent URLs.
