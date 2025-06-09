from typing import List

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile, status

# Prometheus metrics
from app.metrics import (
    INFERENCE_DURATION,
    INFERENCE_REQUESTS,
)
from app.models import resnet
from app.models.multimodel import ModelManager
from app.models.tritonservice import TritonMultiModel

router = APIRouter()
logger = structlog.get_logger()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}

triton_multi_model = TritonMultiModel("triton_cpu:8000")


def return_the_highest_confidence(predictions: List) -> dict | None:
    """
    Find the prediction with the highest confidence.

    Args:
        predictions (list): List of prediction dictionaries.

    Returns:
        dict: The prediction with the highest confidence.
    """
    if not predictions:
        return None
    return max(predictions, key=lambda x: x["confidence"])


@router.post("/predict")
async def predict(file: UploadFile = File(...)) -> dict:
    """
    Endpoint to classify an uploaded image and return the most confident prediction.

    This endpoint accepts an image file (JPEG or PNG), processes it using a ResNet-based
    image classification model, and returns the class label with the highest confidence.

    Args:
        file (UploadFile): The uploaded image file.

    Returns:
        dict: A dictionary containing the most confident prediction:
            {
                "result": {
                    "class_id": str,
                    "class_name": str,
                    "confidence": float
                }
            }

    Raises:
        HTTPException: If the file type is not supported, the file is empty, or
        if an unexpected error occurs during prediction.
    """
    try:
        model_name = "ResNet50"  # Specify the model name for metrics
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning("Unsupported file type", content_type=file.content_type)
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}",
            )

        image_data = await file.read()

        if not image_data:
            logger.warning("Uploaded file is empty")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # Time and count inference
        with INFERENCE_DURATION.labels(model_name=model_name).time():
            pred = resnet.classify_image(image_data)["predictions"]
        INFERENCE_REQUESTS.labels(model_name=model_name, status="success").inc()

        result = return_the_highest_confidence(predictions=pred)
        logger.info("Image classified successfully", result=result)
        return {"result": result}

    except HTTPException as http_exc:
        INFERENCE_REQUESTS.labels(model_name=model_name, status="failure").inc()
        logger.error("HTTPException occurred", detail=http_exc.detail)
        raise http_exc
    except Exception as e:
        INFERENCE_REQUESTS.labels(model_name=model_name, status="failure").inc()
        logger.exception("Unexpected error during prediction: error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


@router.post("/smart_predict")
async def smart_predict(file: UploadFile = File(...)) -> dict:
    """
    Endpoint to classify an uploaded image using the ModelManager's classify_image method.
    This endpoint accepts an image file (JPEG or PNG), processes it using the ModelManager,
    and returns the class label with the highest confidence.
    Args:
        file (UploadFile): The uploaded image file.
    Returns:
        dict: A dictionary containing the most confident prediction:
            {
                "result": {
                    "class_id": str,
                    "class_name": str,
                    "confidence": float,
                    "model_used": str
                }
    Raises:
        HTTPException: If the file type is not supported, the file is empty, or
        if an unexpected error occurs during prediction.
    """
    # For now, we just call the same predict function
    # 1) Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning("Unsupported file type", content_type=file.content_type)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # 2) Read bytes
    image_data = await file.read()
    if not image_data:
        logger.warning("Uploaded file is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    try:
        with INFERENCE_DURATION.labels(model_name="multi").time():
            out = await ModelManager.classify_image(image_data)
        INFERENCE_REQUESTS.labels(model_name=out["model_used"], status="success").inc()

        best = return_the_highest_confidence(out["predictions"])
        # Optionally attach which backbone was used:
        best["model_used"] = out["model_used"]

        logger.info("Image classified successfully (smart_predict)", result=best)
        return {"result": best}

    except HTTPException as http_exc:
        INFERENCE_REQUESTS.labels(model_name="multi", status="failure").inc()
        logger.error("HTTPException in smart_predict", detail=http_exc.detail)
        raise
    except Exception as e:
        INFERENCE_REQUESTS.labels(model_name="multi", status="failure").inc()
        logger.exception("Unexpected error during smart_predict", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


@router.post("/triton_predict")
async def triton_predict(file: UploadFile = File(...)) -> dict:
    """
    Endpoint to classify an uploaded image using the Triton service.
    This endpoint accepts an image file (JPEG or PNG), processes it using the Triton service,
    and returns the class label with the highest confidence.
    Args:
        file (UploadFile): The uploaded image file.
    Returns:
        dict: A dictionary containing the most confident prediction:
            {
                "result": {
                    "class_id": str,
                    "class_name": str,
                    "confidence": float,
                    "model_used": str
                }
    Raises:
        HTTPException: If the file type is not supported, the file is empty, or
        if an unexpected error occurs during prediction.
    """
    try:
        model_label = "triton_multi"  # Specify the model class for metrics
        image_data = await file.read()

        with INFERENCE_DURATION.labels(model_name=model_label).time():
            result = await triton_multi_model.classify_image(image_data)
        INFERENCE_REQUESTS.labels(
            model_name=result["model_used"], status="success"
        ).inc()

        logger.info("Image classified successfully using Triton", result=result)
        best = return_the_highest_confidence(result["predictions"])

        # Optionally attach which backbone was used:
        best["model_used"] = result["model_used"]

        return {"result": best}
    except Exception as e:
        INFERENCE_REQUESTS.labels(model_name=model_label, status="failure").inc()
        logger.exception("Unexpected error during Triton prediction", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during Triton prediction.",
        )
