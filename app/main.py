import os
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from opentelemetry import metrics as otel_metrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app

from app.api.v1.routes import img_class
from app.config.logger import configure_logging

# from prometheus_fastapi_instrumentator import Instrumentator # Uncomment if you want to use the instrumentator instead of the custom metrics
from app.metrics import (  # MODEL_LOAD_TIME,; INFERENCE_REQUESTS,; INFERENCE_DURATION,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS,
    TOTAL_MODEL_LOAD_TIME,
)
from app.models.multimodel import ModelManager

# Configure logger specifically for this class
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
configure_logging(log_folder="logs", log_file_name="main.log")
logger = structlog.get_logger()
getattr(logger, LOG_LEVEL, logger.info)("Logger initialized", log_level=LOG_LEVEL)

OTEL_SERVICE_URL = os.getenv("OTEL_SERVICE_URL", "otel-collector")
OTEL_SERVICE_PORT = os.getenv("OTEL_SERVICE_PORT", "4317")
# Set up the OpenTelemetry exporter endpoint
OTEL_ENDPOINT = f"http://{OTEL_SERVICE_URL}:{OTEL_SERVICE_PORT}"

# Create the logger
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # measure model loading
    start = time.time()
    ModelManager.load_all_models()  # this populates the internal cache, returns None
    duration = time.time() - start
    TOTAL_MODEL_LOAD_TIME.set(duration)
    yield
    # Cleanup models
    ModelManager.clear()


app = FastAPI(
    title="(Ocean Infinity) Marine Image Classifier",
    description="Classifies marine animal images using  pre-trained ImageNet models.",
    version="1.0.1",
    lifespan=lifespan,
    redoc_url="/redoc",
)

# (optional) use FastAPI to expose Prometheus metrics
# Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# Initialize OpenTelemetry instrumentation
resource = Resource.create(
    {
        "service.name": "marine-classifier-api",
        "service.version": "0.0.1",
    }
)

trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_span_exporter = OTLPSpanExporter(
    endpoint=OTEL_ENDPOINT,
    insecure=True,
)
span_processor = BatchSpanProcessor(otlp_span_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=5000,
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
otel_metrics.set_meter_provider(meter_provider)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(
    app,
)
# Add OpenTelemetry middleware to the app
app.add_middleware(OpenTelemetryMiddleware)
# i will use the custom one for the challenge to show skill:
# Expose Prometheus metrics endpoint
app.mount("/metrics", make_asgi_app())


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    method = request.method

    # Start histogram timer
    with HTTP_REQUEST_DURATION.labels(endpoint=endpoint).time():
        response: Response = await call_next(request)

    # Increment total requests counter
    HTTP_REQUESTS.labels(
        method=method, endpoint=endpoint, http_status=response.status_code
    ).inc()

    return response


# Include the API router
app.include_router(img_class.router, prefix="/api/v1", tags=["Image Classification"])


@app.get("/healthz", include_in_schema=False)
async def health_check():
    """
    Health check endpoint to verify the application is running.
    Returns a 200 status if the app is healthy.
    """
    return {"status": "healthy"}


@app.get("/readiness", include_in_schema=False)
async def readiness_check():
    """
    Readiness check endpoint to verify the application is ready to serve traffic.
    Checks if all models are loaded and ready.
    """
    if ModelManager.is_ready():
        return {"status": "ready"}
    return Response(content="Not Ready", status_code=503)


# redirect to redoc documentation
@app.get("/", include_in_schema=False)
async def redirect_to_redoc():
    return RedirectResponse(url="/redoc")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=29000,
        reload=True,
        reload_dirs=["app"],
    )
