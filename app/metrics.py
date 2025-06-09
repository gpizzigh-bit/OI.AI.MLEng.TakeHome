# app/metrics.py
from prometheus_client import Counter, Gauge, Histogram

# ─── HTTP ───────────────────────────────────────────────────────────────────────

# Total HTTP requests received, labeled by method, path, and status code.
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"],
)

# Request duration histogram, by endpoint (seconds).
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Histogram of HTTP request durations",
    ["endpoint"],
)

# ─── MODEL LOADING ──────────────────────────────────────────────────────────────

# Gauge for how long each model takes to load at startup (seconds).
MODEL_LOAD_TIME = Gauge(
    "model_load_duration_seconds",
    "Time taken to load each model on startup",
    ["model_name"],
)

# ─── INFERENCE ─────────────────────────────────────────────────────────────────

# Total inference requests, labeled by model and outcome.
INFERENCE_REQUESTS = Counter(
    "inference_requests_total",
    "Total number of inference requests",
    ["model_name", "status"],
)

# Inference duration histogram, by model (seconds).
INFERENCE_DURATION = Histogram(
    "inference_duration_seconds",
    "Histogram of inference call durations",
    ["model_name"],
)

TOTAL_MODEL_LOAD_TIME = Gauge(
    "marine_classifier_model_load_seconds",
    "Time to load all models at startup",
)
