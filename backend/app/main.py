"""
Oil Trading Dashboard — FastAPI Backend Application.
Production-grade backend with unified adapter architecture, WebSockets,
FinBERT sentiment analysis, signal audit trail, and full observability.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings

settings = get_settings()

# Setup logging BEFORE importing modules that use structlog
from app.observability.logging import setup_logging, CorrelationIDMiddleware
setup_logging(settings.log_level)

from app.cache import cache
from app.adapters import register_all_adapters
from app.api.v1.router import router as v1_router
from app.api.websocket_manager import ws_manager

import structlog
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # ── Startup ──
    background_tasks = []

    # Connect Redis (non-fatal if unavailable)
    try:
        await cache.connect()
        if cache.client:
            ws_manager.set_redis(cache.client)
            # Start WebSocket Redis listener only if Redis is available
            ws_task = asyncio.create_task(ws_manager.start_redis_listener())
            background_tasks.append(ws_task)
    except Exception as e:
        logger.warning("redis_startup_failed_continuing_without_cache", error=str(e))

    # Register all adapters with fallback chains
    register_all_adapters()

    # Initialize news loop in background
    try:
        from app.adapters.news_feed import feed

        async def news_loop():
            while True:
                try:
                    await feed.refresh()
                except Exception:
                    pass
                await asyncio.sleep(60)  # refresh every minute

        news_task = asyncio.create_task(news_loop())
        background_tasks.append(news_task)
    except Exception as e:
        logger.warning("news_startup_failed", error=str(e))

    # Initialize Paper Trading Engine
    try:
        from app.services.trading.orchestrator import start_trading_engine
        from app.services.trading.state_manager import state_manager
        
        start_trading_engine()
        
        trading_task = asyncio.create_task(state_manager.poll_data())
        background_tasks.append(trading_task)
    except Exception as e:
        logger.error(f"trading_engine_startup_failed: {e}")

    yield

    # ── Shutdown ──
    for task in background_tasks:
        task.cancel()
    await cache.close()


app = FastAPI(
    title="Oil Trading Dashboard API",
    description="Production-grade backend for the Quant Oil Desk trading dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CorrelationIDMiddleware)

# ── Prometheus ──
if settings.prometheus_enabled:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ── Routes ──
app.include_router(v1_router)


@app.get("/")
async def root():
    return {
        "service": "Oil Trading Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
