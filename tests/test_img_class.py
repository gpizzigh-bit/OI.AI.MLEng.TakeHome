from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.api.v1.routes.img_class import return_the_highest_confidence, router

# Setup FastAPI app for testing

app = FastAPI()
app.include_router(router, prefix="/api/v1")


@pytest.mark.asyncio
async def test_return_the_higest_confidence_normal():
    predictions = [
        {"class_id": "1", "class_name": "cat", "confidence": 0.7},
        {"class_id": "2", "class_name": "dog", "confidence": 0.9},
        {"class_id": "3", "class_name": "bird", "confidence": 0.2},
    ]
    result = return_the_highest_confidence(predictions)
    assert result["class_id"] == "2"
    assert result["confidence"] == 0.9


@pytest.mark.asyncio
async def test_return_the_higest_confidence_empty():
    assert return_the_highest_confidence([]) is None


@pytest.mark.asyncio
async def test_return_the_higest_confidence_none():
    assert return_the_highest_confidence(None) is None


app = FastAPI()
app.include_router(router, prefix="/api/v1")


@pytest.mark.asyncio
@patch("app.api.v1.routes.img_class.resnet")
async def test_predict_success(mock_resnet):
    def mock_classify_image(data):
        return {
            "predictions": [
                {"class_id": "1", "class_name": "cat", "confidence": 0.7},
                {"class_id": "2", "class_name": "dog", "confidence": 0.9},
            ]
        }

    mock_resnet.classify_image = MagicMock(side_effect=mock_classify_image)
    file_content = b"fake image data"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/predict", files=files)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["class_id"] == "2"
    assert result["class_name"] == "dog"
    assert result["confidence"] == 0.9


@pytest.mark.asyncio
@patch("app.api.v1.routes.img_class.resnet")
async def test_predict_unsupported_media_type(mock_resnet):
    file_content = b"fake image data"
    files = {"file": ("test.txt", file_content, "text/plain")}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/predict", files=files)
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
@patch("app.api.v1.routes.img_class.resnet")
async def test_predict_empty_file(mock_resnet):
    files = {"file": ("test.jpg", b"", "image/jpeg")}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/predict", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Uploaded file is empty" in response.json()["detail"]


@pytest.mark.asyncio
@patch("app.api.v1.routes.img_class.resnet")
async def test_predict_internal_error(mock_resnet):
    def raise_exception(data):
        raise Exception("fail")

    mock_resnet.classify_image = MagicMock(side_effect=raise_exception)
    file_content = b"fake image data"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/predict", files=files)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "unexpected error" in response.json()["detail"].lower()
