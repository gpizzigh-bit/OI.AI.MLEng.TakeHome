import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
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
configure_logging(log_folder="logs", log_file_name="main.log")

# Create the logger
logger = structlog.get_logger()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     ModelManager.load_all_models()
#     yield
#     # Cleanup models
#     ModelManager.clear()


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
    description="Classifies marine animal images using a pre-trained ImageNet model soup (BASIC-L).",
    version="0.0.1",
    lifespan=lifespan,
)

# (optional) use FastAPI to expose Prometheus metrics
# Instrumentator().instrument(app).expose(app, endpoint="/metrics")

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
