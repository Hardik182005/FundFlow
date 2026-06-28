import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from services.news_service import fetch_news


async def main():
    articles = await fetch_news()
    print(f"articles: {len(articles)}")
    for a in articles[:5]:
        print(f"  [{a['source']}] {a['title'][:70]} ({a['published'][:25]})")


asyncio.run(main())
