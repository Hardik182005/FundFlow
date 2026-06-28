"""Typed async client for the Anakin hosted API (Universal Scraper + Wire).

Anti-hallucination guardrails:
- This client never fabricates scrape content or Wire results. On any failure it
  returns a result object with status != "completed" and an error string.
- API keys are never logged.
- Wire action IDs are never invented; callers must pass IDs discovered from the
  Wire catalog/search API.

Endpoint contract (per Anakin hosted API):
    POST /url-scraper            -> { jobId }
    GET  /url-scraper/{jobId}    -> { status, markdown, json, credits, ... }
    GET  /wire/search?q=         -> { actions: [...] }
    GET  /wire/catalog/{slug}    -> { actions: [...] }
    POST /wire/task              -> { jobId }
    GET  /wire/jobs/{jobId}      -> { status, data, ... }

Field names are parsed defensively (several common aliases) so small response
shape differences do not crash the pipeline.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, List

import httpx

from config import settings
from models.audit_schemas import (
    AnakinJobSubmission,
    AnakinScrapeResult,
    WireAction,
    WireCatalog,
    WireJobSubmission,
    WireJobResult,
)

logger = logging.getLogger("fundflow.anakin")

USER_AGENT = "FundFlow-Audit/1.0 (+https://fundflow.app)"
_POLL_INTERVALS = [2, 2, 3, 3, 5, 5, 8]  # exponential-ish backoff, seconds


class AnakinError(Exception):
    """Raised for non-recoverable Anakin errors (sanitized message)."""

    def __init__(self, message: str, status_code: Optional[int] = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class InsufficientCreditError(AnakinError):
    def __init__(self, message: str = "Anakin credit budget exceeded for this operation."):
        super().__init__(message, status_code=402, retryable=False)


def _first(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return default


def _sanitize(detail: str) -> str:
    """Strip anything that could leak a key or internal payload."""
    if not detail:
        return "Anakin request failed."
    text = str(detail)
    if settings.ANAKIN_API_KEY and settings.ANAKIN_API_KEY in text:
        text = text.replace(settings.ANAKIN_API_KEY, "***")
    return text[:300]


class AnakinClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.ANAKIN_API_KEY
        self.base_url = (base_url or settings.ANAKIN_API_BASE).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    async def _request(self, method: str, path: str, *, json: dict | None = None,
                       params: dict | None = None, max_retries: int = 3) -> dict:
        if not self.configured:
            raise AnakinError("Anakin is not configured (missing ANAKIN_API_KEY).", status_code=401)

        url = f"{self.base_url}{path}"
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt < max_retries:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.request(method, url, headers=self._headers(),
                                                json=json, params=params)
                if resp.status_code in (401, 403):
                    raise AnakinError("Anakin authentication failed.", status_code=resp.status_code)
                if resp.status_code == 402:
                    raise InsufficientCreditError()
                if resp.status_code == 404:
                    raise AnakinError("Anakin resource not found.", status_code=404)
                if resp.status_code == 422:
                    raise AnakinError("Anakin rejected the request parameters.", status_code=422)
                if resp.status_code == 429:
                    # rate limited -> backoff & retry
                    await asyncio.sleep(min(2 * attempt, 8))
                    last_exc = AnakinError("Anakin rate limit.", status_code=429, retryable=True)
                    continue
                if resp.status_code >= 500:
                    await asyncio.sleep(min(2 * attempt, 8))
                    last_exc = AnakinError("Anakin service error.", status_code=resp.status_code, retryable=True)
                    continue
                if resp.status_code >= 400:
                    # Convert any remaining non-2xx into a sanitized AnakinError so
                    # httpx.HTTPStatusError never leaks out of the client.
                    raise AnakinError(f"Anakin returned HTTP {resp.status_code}.",
                                      status_code=resp.status_code)
                try:
                    return resp.json()
                except Exception:
                    return {"raw": resp.text}
            except (httpx.TransportError, httpx.TimeoutException) as e:
                last_exc = e
                await asyncio.sleep(min(2 * attempt, 8))
                continue
            except InsufficientCreditError:
                raise
            except AnakinError:
                raise
        # exhausted retries
        msg = _sanitize(str(last_exc) if last_exc else "Anakin request failed after retries.")
        raise AnakinError(msg, retryable=True)

    # ----------------------- Universal Scraper -----------------------

    async def submit_scrape(self, url: str, use_browser: bool = False,
                            generate_json: bool = False) -> AnakinJobSubmission:
        payload = {"url": url, "useBrowser": use_browser, "generateJson": generate_json}
        data = await self._request("POST", "/url-scraper", json=payload)
        job_id = _first(data, "jobId", "job_id", "id", default="")
        return AnakinJobSubmission(job_id=str(job_id), status=_first(data, "status", default="submitted"),
                                   source_url=url)

    async def get_scrape_job(self, job_id: str) -> AnakinScrapeResult:
        data = await self._request("GET", f"/url-scraper/{job_id}")
        status = str(_first(data, "status", default="unknown")).lower()
        return AnakinScrapeResult(
            job_id=job_id,
            status=status,
            cached=bool(_first(data, "cached", "cache", default=False)),
            markdown=_first(data, "markdown", "content", "text"),
            generated_json=_first(data, "json", "generatedJson", "data"),
            source_url=_first(data, "url", "source_url"),
            error=_sanitize(_first(data, "error", "message")) if status in ("failed", "error") else None,
        )

    async def scrape_url(self, url: str, use_browser: bool = False,
                         generate_json: bool = False, timeout_seconds: int = 90) -> AnakinScrapeResult:
        start = time.monotonic()
        try:
            sub = await self.submit_scrape(url, use_browser, generate_json)
        except AnakinError as e:
            return AnakinScrapeResult(source_url=url, status="error", error=_sanitize(str(e)))

        result = await self._poll_scrape(sub.job_id, url, timeout_seconds)
        result.duration_seconds = round(time.monotonic() - start, 2)
        result.used_browser = use_browser
        return result

    async def _poll_scrape(self, job_id: str, url: str, timeout_seconds: int) -> AnakinScrapeResult:
        deadline = time.monotonic() + timeout_seconds
        i = 0
        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_INTERVALS[min(i, len(_POLL_INTERVALS) - 1)])
            i += 1
            try:
                res = await self.get_scrape_job(job_id)
            except AnakinError as e:
                return AnakinScrapeResult(job_id=job_id, source_url=url, status="error", error=_sanitize(str(e)))
            if res.status in ("completed", "success", "done"):
                res.status = "completed"
                res.source_url = res.source_url or url
                return res
            if res.status in ("failed", "error"):
                res.source_url = res.source_url or url
                return res
        return AnakinScrapeResult(job_id=job_id, source_url=url, status="timeout",
                                  error="Anakin did not return content within the time limit.")

    async def scrape_batch(self, urls: List[str], use_browser: bool = False,
                           generate_json: bool = False) -> List[AnakinScrapeResult]:
        tasks = [self.scrape_url(u, use_browser, generate_json) for u in urls]
        return list(await asyncio.gather(*tasks))

    # ----------------------- Wire -----------------------

    @staticmethod
    def _parse_wire_action(a: dict) -> WireAction:
        return WireAction(
            action_id=str(_first(a, "actionId", "action_id", "id", default="")),
            catalog=_first(a, "catalog", "slug", "site"),
            name=_first(a, "name", "title", default="Unnamed action"),
            description=_first(a, "description", "desc"),
            param_schema=_first(a, "paramSchema", "parameters", "input_schema", default={}) or {},
            output_schema=_first(a, "outputSchema", "output_schema", default={}) or {},
            credits_per_call=_first(a, "credits", "creditsPerCall", "cost"),
        )

    async def search_wire_actions(self, query: str, catalog: Optional[str] = None) -> List[WireAction]:
        params = {"q": query}
        if catalog:
            params["catalog"] = catalog
        data = await self._request("GET", "/wire/search", params=params)
        actions = _first(data, "actions", "results", "data", default=[]) or []
        return [self._parse_wire_action(a) for a in actions if isinstance(a, dict)]

    async def get_wire_catalog(self, slug: str) -> WireCatalog:
        data = await self._request("GET", f"/wire/catalog/{slug}")
        actions = _first(data, "actions", "results", default=[]) or []
        return WireCatalog(slug=slug, actions=[self._parse_wire_action(a) for a in actions if isinstance(a, dict)])

    async def execute_wire_task(self, action_id: str, params: dict,
                                credential_id: Optional[str] = None) -> WireJobSubmission:
        if not action_id:
            raise AnakinError("A Wire action id is required (never invent one).", status_code=422)
        payload = {"actionId": action_id, "params": params}
        if credential_id:
            payload["credentialId"] = credential_id
        data = await self._request("POST", "/wire/task", json=payload)
        return WireJobSubmission(job_id=str(_first(data, "jobId", "job_id", "id", default="")),
                                 status=_first(data, "status", default="submitted"), action_id=action_id)

    async def get_wire_job(self, job_id: str) -> WireJobResult:
        data = await self._request("GET", f"/wire/jobs/{job_id}")
        status = str(_first(data, "status", default="unknown")).lower()
        return WireJobResult(
            job_id=job_id, status=status,
            data=_first(data, "data", "result", "output"),
            error=_sanitize(_first(data, "error", "message")) if status in ("failed", "error") else None,
        )

    async def execute_wire_and_wait(self, action_id: str, params: dict,
                                    credential_id: Optional[str] = None,
                                    timeout_seconds: int = 90) -> WireJobResult:
        start = time.monotonic()
        try:
            sub = await self.execute_wire_task(action_id, params, credential_id)
        except AnakinError as e:
            return WireJobResult(action_id=action_id, status="error", error=_sanitize(str(e)))
        deadline = time.monotonic() + timeout_seconds
        i = 0
        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_INTERVALS[min(i, len(_POLL_INTERVALS) - 1)])
            i += 1
            try:
                res = await self.get_wire_job(sub.job_id)
            except AnakinError as e:
                return WireJobResult(job_id=sub.job_id, action_id=action_id, status="error", error=_sanitize(str(e)))
            if res.status in ("completed", "success", "done"):
                res.status = "completed"
                res.action_id = action_id
                res.duration_seconds = round(time.monotonic() - start, 2)
                return res
            if res.status in ("failed", "error"):
                res.action_id = action_id
                return res
        return WireJobResult(job_id=sub.job_id, action_id=action_id, status="timeout",
                             error="Wire action did not complete within the time limit.")


# module-level singleton
anakin_client = AnakinClient()
