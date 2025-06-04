import structlog
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions

# Initialize the logger
logger = structlog.get_logger()

# Load the ResNet50 model with ImageNet weights
model = tf.keras.applications.ResNet50(weights="imagenet")

# Define target image size for ResNet50
TARGET_SIZE = (224, 224)

def classify_image(image_data: bytes) -> dict:
    """
    Classify an image using the ResNet50 model. Tensorflow will be used for asynchronous inference.
    So this function must reamin synchronous. as not to interfere with the async inferece of tensorflow model.

    Args:
        image_data (bytes): The image data in bytes.

    Returns:
        dict: A dictionary containing the top-5 predicted classes and their probabilities.
    """
    logger.info("classify_image called with image data of length", length=len(image_data))

    # Preprocess the image
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    image = image.resize(TARGET_SIZE)
    image_array = np.array(image)
    image_batch = np.expand_dims(image_array, axis=0)
    preprocessed_image = preprocess_input(image_batch)

    # Perform inference asynchronously
    predictions = tf.constant(predictions := model(preprocessed_image))

    # Decode predictions (top-5)
    decoded = decode_predictions(predictions.numpy(), top=5)[0]

    # Structure results
    results = [
        {"class_id": class_id, "class_name": class_name, "confidence": float(confidence)}
        for (class_id, class_name, confidence) in decoded
    ]

    logger.info("classification result", results=results)

    return {"predictions": results}

