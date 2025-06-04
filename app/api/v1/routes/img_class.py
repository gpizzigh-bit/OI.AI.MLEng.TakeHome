# app/routes.py

from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models import resnet
import structlog

router = APIRouter()
logger = structlog.get_logger()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


def return_the_higest_confidence(predictions: List) -> dict | None:
    """
    Find the prediction with the highest confidence.
    
    Args:
        predictions (list): List of prediction dictionaries.
        
    Returns:
        dict: The prediction with the highest confidence.
    """
    if not predictions:
        return None
    return max(predictions, key=lambda x: x['confidence'])

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
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )

        image_data = await file.read()

        if not image_data:
            logger.warning("Uploaded file is empty")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        result = return_the_higest_confidence(resnet.classify_image(image_data)['predictions'])
        logger.info("Image classified successfully", result=result)
        return {"result": result}

    except HTTPException as http_exc:
        logger.error("HTTPException occurred", detail=http_exc.detail)
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error during prediction: error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction."
        )
