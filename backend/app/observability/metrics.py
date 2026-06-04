"""Prometheus metric definitions for the oil trading dashboard."""

from prometheus_client import Counter, Histogram, Gauge

# ── HTTP Request Metrics ──
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── Cache Metrics ──
CACHE_HIT = Counter("cache_hits_total", "Cache hits", ["endpoint"])
CACHE_MISS = Counter("cache_misses_total", "Cache misses", ["endpoint"])

# ── Adapter Metrics ──
ADAPTER_REQUEST = Counter(
    "adapter_requests_total",
    "Adapter call count",
    ["adapter", "status"],
)
ADAPTER_LATENCY = Histogram(
    "adapter_request_seconds",
    "Adapter response time",
    ["adapter"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)
ADAPTER_STATUS = Gauge(
    "adapter_status",
    "Current adapter status (1=live, 0=down)",
    ["adapter"],
)

# ── WebSocket Metrics ──
WS_CONNECTIONS = Gauge(
    "ws_active_connections",
    "Active WebSocket connections",
    ["room"],
)
WS_MESSAGES_SENT = Counter(
    "ws_messages_sent_total",
    "Messages pushed via WebSocket",
    ["room"],
)

# ── Celery Metrics ──
CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Task execution time",
    ["task_name"],
)

# ── Signal Engine Metrics ──
SIGNAL_GENERATED = Counter(
    "signal_generated_total",
    "Signals generated",
    ["direction", "conviction"],
)

# ── FinBERT Metrics ──
FINBERT_LATENCY = Histogram(
    "finbert_inference_seconds",
    "FinBERT inference time per batch",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
