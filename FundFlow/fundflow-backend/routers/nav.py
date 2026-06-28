from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.schemas import SearchResult, FundMeta, NavEntry
from services.amfi_service import search_funds, get_latest_nav, get_nav_history

router = APIRouter()


@router.get("/search", response_model=List[SearchResult])
async def search_fund(q: str = Query(..., min_length=2)):
    results = await search_funds(q)
    if not results:
        return []
    return results


@router.get("/{scheme_code}", response_model=FundMeta)
async def get_nav(scheme_code: str):
    data = await get_latest_nav(scheme_code)
    if not data:
        raise HTTPException(status_code=404, detail="NAV data not found. Try again shortly.")
    return data


@router.get("/{scheme_code}/history", response_model=List[NavEntry])
async def get_history(scheme_code: str, days: int = Query(default=365, ge=1, le=1825)):
    history = await get_nav_history(scheme_code, days)
    if not history:
        raise HTTPException(status_code=404, detail="No NAV history found.")
    return history


@router.post("/refresh")
async def trigger_refresh():
    """Manually trigger AMFI NAV refresh + update all portfolio snapshots in Firestore."""
    from services.amfi_service import refresh_nav_cache
    import asyncio
    asyncio.create_task(refresh_nav_cache())
    return {"message": "AMFI NAV refresh started. All portfolio values will update with latest AMFI data."}


@router.get("/cache/status")
async def cache_status():
    """Return how many scheme codes are currently cached and their freshness."""
    from services.amfi_service import _nav_cache
    from datetime import datetime
    status = []
    for code, entry in _nav_cache.items():
        cached_at = entry.get("cached_at")
        age_mins = round((datetime.now() - cached_at).total_seconds() / 60, 1) if cached_at else None
        status.append({
            "scheme_code": code,
            "scheme_name": entry.get("scheme_name", ""),
            "nav": entry.get("nav"),
            "nav_date": entry.get("nav_date"),
            "cache_age_minutes": age_mins,
        })
    return {"cached_schemes": len(status), "entries": status}
