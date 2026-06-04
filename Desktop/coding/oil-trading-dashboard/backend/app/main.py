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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # ── Startup ──

    # Connect Redis
    await cache.connect()
    ws_manager.set_redis(cache.client)

    # Register all adapters with fallback chains
    register_all_adapters()

    # Start WebSocket Redis listener in background
    ws_task = asyncio.create_task(ws_manager.start_redis_listener())

    # Initialize FinBERT in background to avoid blocking startup
    from app.analytics.sentiment import init_finbert
    from app.adapters.news_feed import feed
    
    async def init_nlp():
        await asyncio.to_thread(init_finbert)
    
    async def news_loop():
        while True:
            try:
                await feed.refresh()
            except Exception:
                pass
            await asyncio.sleep(60) # refresh every minute
            
    asyncio.create_task(init_nlp())
    news_task = asyncio.create_task(news_loop())

    yield

    # ── Shutdown ──
    ws_task.cancel()
    news_task.cancel()
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
