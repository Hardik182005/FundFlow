from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os

from routers import nav, portfolio, analysis, news, voice, audit, assistant, anakin, sources
from services.amfi_service import refresh_nav_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

_IS_LAMBDA = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The APScheduler background job only makes sense on a long-running server,
    # not on Lambda (no persistent event loop between invocations).
    if not _IS_LAMBDA:
        scheduler.add_job(
            refresh_nav_cache,
            CronTrigger(hour=18, minute=0, day_of_week="mon-fri"),
            id="nav_refresh",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduler started")
    yield
    if not _IS_LAMBDA and scheduler.running:
        scheduler.shutdown()

app = FastAPI(
    title="FundFlow API",
    description="Mutual Fund Portfolio Tracker API — powered by AMFI India & Groq AI",
    version="1.0.0",
    lifespan=lifespan,
)

_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins = [o.strip() for o in _origins_raw.split(",")] if _origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nav.router, prefix="/api/nav", tags=["NAV"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(audit.router, prefix="/api/audit", tags=["Fund Audit"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["Assistant"])
app.include_router(anakin.router, prefix="/api/anakin", tags=["Anakin"])
app.include_router(sources.router, prefix="/api/sources", tags=["Fund Sources"])

@app.get("/")
async def root():
    return {"message": "FundFlow API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/health/dependencies")
async def dependency_health():
    """Configuration-presence check only — never spends Anakin credits."""
    from config import settings
    return {
        "status": "ok",
        "anakin_configured": settings.anakin_configured,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "elevenlabs_configured": bool(settings.ELEVENLABS_API_KEY),
        "persistence": "in-memory",
        "demo_mode": settings.DEMO_MODE,
    }


# AWS Lambda entrypoint (container image + Function URL). Harmless when unused.
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:  # mangum not installed in local dev
    handler = None
