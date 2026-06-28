from fastapi import APIRouter
from typing import List
from models.schemas import NewsArticle
from services.news_service import fetch_news

router = APIRouter()


@router.get("", response_model=List[NewsArticle])
async def get_news():
    articles = await fetch_news()
    return articles
