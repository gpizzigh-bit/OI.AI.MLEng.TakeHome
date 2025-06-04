from fastapi import FastAPI
from app.api.v1.routes import img_class
from app.config import logger
from fastapi.responses import RedirectResponse

# configure logging
logger.configure_logging()

app = FastAPI(
    title="(Ocean Infinity) Marine Image Classifier",
    description="Classifies marine animal images using a pre-trained ImageNet model soup (BASIC-L).",
    version="0.0.1"
)

# Include the API router
app.include_router(img_class.router, prefix="/api/v1", tags=["Image Classification"])

# redirect to redoc documentation
@app.get("/", include_in_schema=False)
async def redirect_to_redoc():
    return RedirectResponse(url="/redoc")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
