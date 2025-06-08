# app/routes.py

from typing import List

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile, status

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

        result = return_the_highest_confidence(
            resnet.classify_image(image_data)["predictions"]
        )
        logger.info("Image classified successfully", result=result)
        return {"result": result}

    except HTTPException as http_exc:
        logger.error("HTTPException occurred", detail=http_exc.detail)
        raise http_exc
    except Exception as e:
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
        # 3) Delegate to ModelManager.classify_image
        out = await ModelManager.classify_image(image_data)
        # out is {"model_used": "...", "predictions": [ {...}, ... ]}

        best = return_the_highest_confidence(out["predictions"])
        # Optionally attach which backbone was used:
        best["model_used"] = out["model_used"]

        logger.info("Image classified successfully (smart_predict)", result=best)
        return {"result": best}

    except ValueError as ve:
        logger.error("PIL decode error or invalid image", error=str(ve))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
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
        image_data = await file.read()
        result = await triton_multi_model.classify_image(image_data)
        logger.info("Image classified successfully using Triton", result=result)
        return result
    except Exception as e:
        logger.exception("Unexpected error during Triton prediction", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during Triton prediction.",
        )
