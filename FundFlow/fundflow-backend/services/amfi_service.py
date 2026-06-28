import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

MFAPI_BASE = "https://api.mfapi.in/mf"
AMFI_DIRECT_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# In-memory cache: { scheme_code: { nav, date, cached_at, meta } }
_nav_cache: Dict[str, Dict[str, Any]] = {}

CACHE_TTL_HOURS = 12


def _is_cache_valid(entry: Dict) -> bool:
    if not entry:
        return False
    cached_at = entry.get("cached_at")
    if not cached_at:
        return False
    age_hours = (datetime.now() - cached_at).total_seconds() / 3600
    return age_hours < CACHE_TTL_HOURS


async def search_funds(query: str) -> List[Dict]:
    url = f"{MFAPI_BASE}/search?q={query.replace(' ', '+')}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return [{"schemeCode": str(item["schemeCode"]), "schemeName": item["schemeName"]} for item in data]
        except Exception as e:
            logger.error(f"Fund search failed: {e}")
            return []


async def get_latest_nav(scheme_code: str) -> Optional[Dict]:
    if scheme_code in _nav_cache and _is_cache_valid(_nav_cache[scheme_code]):
        return _nav_cache[scheme_code]

    try:
        data = await _fetch_from_mfapi(scheme_code)
        if data:
            _nav_cache[scheme_code] = {**data, "cached_at": datetime.now()}
            return data
    except Exception as e:
        logger.warning(f"mfapi.in failed for {scheme_code}: {e}. Falling back to AMFI direct.")

    return await _fetch_from_amfi_direct(scheme_code)


async def _fetch_from_mfapi(scheme_code: str) -> Optional[Dict]:
    url = f"{MFAPI_BASE}/{scheme_code}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()
        meta = body.get("meta", {})
        data = body.get("data", [])
        if not data:
            return None
        latest = data[0]
        return {
            "scheme_code": scheme_code,
            "scheme_name": meta.get("scheme_name", ""),
            "nav": float(latest["nav"]),
            "nav_date": latest["date"],
            "category": meta.get("scheme_category", ""),
            "amc": meta.get("fund_house", ""),
        }


async def _fetch_from_amfi_direct(scheme_code: str) -> Optional[Dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(AMFI_DIRECT_URL)
            resp.raise_for_status()
            lines = resp.text.splitlines()
            for line in lines:
                parts = line.split(";")
                if len(parts) >= 7 and parts[0].strip() == scheme_code:
                    return {
                        "scheme_code": scheme_code,
                        "scheme_name": parts[3].strip(),
                        "nav": float(parts[6].strip()),
                        "nav_date": parts[5].strip(),
                        "category": "",
                        "amc": "",
                    }
        except Exception as e:
            logger.error(f"AMFI direct fetch failed: {e}")
    return None


async def get_nav_history(scheme_code: str, days: int = 365) -> List[Dict]:
    url = f"{MFAPI_BASE}/{scheme_code}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            body = resp.json()
            data = body.get("data", [])
            sliced = data[:days]
            return [{"date": item["date"], "nav": float(item["nav"])} for item in sliced]
        except Exception as e:
            logger.error(f"NAV history fetch failed for {scheme_code}: {e}")
            return []


async def get_fund_metadata(scheme_code: str) -> Optional[Dict]:
    """Fetch richer metadata from mfdata.in (expense ratio, rating)."""
    url = f"https://mfdata.in/api/v1/schemes/{scheme_code}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"mfdata.in fetch failed for {scheme_code}: {e}")
    return None


async def refresh_nav_cache():
    """Scheduled daily job (23:30 IST): fetch latest AMFI NAV for all portfolios and update Firestore snapshot."""
    logger.info("Starting scheduled NAV cache refresh from AMFI...")
    from services.store_service import get_all_scheme_codes, update_portfolio_nav_snapshots
    try:
        scheme_codes = await get_all_scheme_codes()
        refreshed = {}
        for code in scheme_codes:
            try:
                data = await _fetch_from_mfapi(code)
                if data:
                    _nav_cache[code] = {**data, "cached_at": datetime.now()}
                    refreshed[code] = data
                    logger.info(f"AMFI NAV refreshed: {code} = {data['nav']} ({data['nav_date']})")
                else:
                    # Fallback to AMFI direct text file
                    data = await _fetch_from_amfi_direct(code)
                    if data:
                        _nav_cache[code] = {**data, "cached_at": datetime.now()}
                        refreshed[code] = data
            except Exception as e:
                logger.warning(f"Failed to refresh NAV for {code}: {e}")

        # Write updated NAV snapshot to Firestore so portfolio valuations are always fresh
        await update_portfolio_nav_snapshots(refreshed)
        logger.info(f"NAV refresh complete. {len(refreshed)}/{len(scheme_codes)} schemes updated.")
    except Exception as e:
        logger.error(f"NAV cache refresh failed: {e}")
