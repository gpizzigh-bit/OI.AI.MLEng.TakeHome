import io

import numpy as np
import structlog
import tensorflow as tf
from opentelemetry import trace
from PIL import Image
from tensorflow.keras.applications.resnet50 import decode_predictions, preprocess_input

tracer = trace.get_tracer(__name__)

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
    with tracer.start_as_current_span("classify_image") as span:
        span.set_attribute("model.name", "ResNet50")
        logger.info(
            "classify_image called with image data of length", length=len(image_data)
        )

        # Preprocessing
        with tracer.start_as_current_span("preprocessing"):
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            image = image.resize(TARGET_SIZE)
            image_array = np.array(image)
            image_batch = np.expand_dims(image_array, axis=0)
            preprocessed_image = preprocess_input(image_batch)

        # Inference
        with tracer.start_as_current_span("inference"):
            predictions = tf.constant(predictions := model(preprocessed_image))

        # Postprocessing / Decoding
        with tracer.start_as_current_span("postprocessing"):
            decoded = decode_predictions(predictions.numpy(), top=5)[0]
            results = [
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": float(confidence),
                }
                for (class_id, class_name, confidence) in decoded
            ]

        # Attach top prediction confidence
        if results:
            span.set_attribute("top_prediction.confidence", results[0]["confidence"])

        logger.info("classification result", results=results)

        return {"predictions": results}
