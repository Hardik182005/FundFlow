import httpx
import feedparser
import logging
import re
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Moneycontrol's MFunds.xml feed returns 503 (blocked) and the old ET /mf/rss.cms
# URL now serves an HTML page, so we use ET's real RSS feed plus Livemint as backup.
# mf_only=False feeds carry general finance news, so they get keyword-filtered to MF topics.
RSS_FEEDS = [
    ("ET Markets", "https://economictimes.indiatimes.com/mf/rssfeeds/359241701.cms", True),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/MFunds.xml", True),
    ("Livemint", "https://www.livemint.com/rss/money", False),
]

MF_KEYWORDS = re.compile(
    r"mutual fund|\bmf\b|\bsip\b|\bnav\b|\belss\b|\bamc\b|\bamfi\b|\bsebi\b"
    r"|equity fund|debt fund|hybrid fund|index fund|flexi.?cap|small.?cap fund|mid.?cap fund"
    r"|large.?cap fund|liquid fund|fund house|folio|\betf\b|expense ratio|new fund offer|\bnfo\b",
    re.IGNORECASE,
)

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_news_cache: List[Dict] = []
_cache_time: float = 0
CACHE_MINUTES = 30

_TAG_RE = re.compile(r"<[^>]+>")


def _is_cache_fresh() -> bool:
    import time
    return (time.time() - _cache_time) < (CACHE_MINUTES * 60)


def _clean_summary(raw: str) -> str:
    text = _TAG_RE.sub("", raw or "").strip()
    if len(text) > 200:
        text = text[:200] + "..."
    return text


async def fetch_news() -> List[Dict]:
    global _news_cache, _cache_time
    import time

    if _news_cache and _is_cache_fresh():
        return _news_cache

    articles = []
    async with httpx.AsyncClient(timeout=20, headers=REQUEST_HEADERS, follow_redirects=True) as client:
        for source_name, feed_url, mf_only in RSS_FEEDS:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
                if not feed.entries:
                    logger.warning(f"RSS feed from {source_name} returned no entries")
                for entry in feed.entries[:15]:
                    title = entry.get("title", "")
                    summary = _clean_summary(getattr(entry, "summary", ""))
                    if not mf_only and not MF_KEYWORDS.search(f"{title} {summary}"):
                        continue
                    articles.append({
                        "title": title,
                        "link": entry.get("link", ""),
                        "summary": summary,
                        "source": source_name,
                        "published": entry.get("published", datetime.now().strftime("%Y-%m-%d")),
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch RSS from {source_name}: {e}")

    def _sort_key(article: Dict):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(article["published"]).timestamp()
        except Exception:
            return 0

    articles.sort(key=_sort_key, reverse=True)
    result = articles[:20]
    if result:
        # Only overwrite the cache with non-empty results so a transient outage
        # doesn't blank the news tab for 30 minutes.
        _news_cache = result
        _cache_time = time.time()
        return _news_cache
    return _news_cache or []
