import io
import json
import threading

import numpy as np
import psutil
from fastapi.concurrency import run_in_threadpool
from opentelemetry import trace
from PIL import Image
from tritonclient.http import (
    InferenceServerClient,
    InferenceServerException,
    InferInput,
    InferRequestedOutput,
)

from app.config.logger import get_class_logger

tracer = trace.get_tracer(__name__)

logger = get_class_logger("TritonMultiModel")

# Load ImageNet class mapping
with open("./app/models/imagenet_class_index.json", "r") as f:
    imagenet_class_index = json.load(f)


class TritonMultiModel:
    CPU_TO_MODEL = [
        (0.30, "ResNet152V2"),
        (0.60, "ResNet50V2"),
        (0.85, "ResNet101V2"),
        (1.00, "ResNet50"),
    ]

    MODEL_INFO = {
        "Xception": {"preprocess": lambda x: x / 255.0, "input_size": (299, 299)},
        "ResNet152V2": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "ResNet101V2": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "ResNet50V2": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "ResNet152": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "ResNet101": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "ResNet50": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "VGG19": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
        "VGG16": {"preprocess": lambda x: x / 255.0, "input_size": (224, 224)},
    }

    _lock = threading.Lock()

    def __init__(self, triton_url: str = "localhost:8000"):
        self.client = InferenceServerClient(url=triton_url)

    @classmethod
    def _choose_model_by_cpu(cls) -> str:
        cpu_pct = psutil.cpu_percent(interval=None) / 100.0
        logger.info("CPU usage measured", cpu_pct=cpu_pct)
        for threshold, model_name in cls.CPU_TO_MODEL:
            if cpu_pct <= threshold:
                return model_name
        return cls.CPU_TO_MODEL[-1][1]

    async def classify_image(self, image_data: bytes) -> dict:
        # Start total span for the whole inference
        with tracer.start_as_current_span("triton_inference") as span:
            span.set_attribute("triton.model.auto_selected", True)

            # Model selection (nested span)
            with tracer.start_as_current_span("model_selection") as selection_span:
                model_name = self._choose_model_by_cpu()
                selection_span.set_attribute("model.name", model_name)
                # Also attach to parent span for higher-level context
                span.set_attribute("model.name", model_name)

            info = self.MODEL_INFO[model_name]
            input_h, input_w = info["input_size"]
            preprocess_fn = info["preprocess"]

            # Preprocessing
            with tracer.start_as_current_span("preprocessing"):
                try:
                    img = Image.open(io.BytesIO(image_data)).convert("RGB")
                except Exception as e:
                    logger.error("Image decode error", error=str(e))
                    raise ValueError(f"Could not decode image bytes: {e}")

                img = img.resize((input_w, input_h))
                x = np.asarray(img, dtype=np.float32)
                x = np.expand_dims(x, axis=0)
                x = preprocess_fn(x)

            # Health check
            with tracer.start_as_current_span("health_check"):
                try:
                    is_ready = await run_in_threadpool(
                        self.client.is_model_ready, model_name
                    )
                    if not is_ready:
                        raise RuntimeError(f"Triton model '{model_name}' is not ready.")
                except InferenceServerException as e:
                    logger.error("Triton health-check error", error=str(e))
                    raise RuntimeError(f"Triton health-check failed: {e}")

            # Inference
            with tracer.start_as_current_span("inference_call"):
                inputs = InferInput("input", x.shape, "FP32")
                inputs.set_data_from_numpy(x)
                outputs = InferRequestedOutput("predictions")
                try:
                    response = await run_in_threadpool(
                        self.client.infer,
                        model_name=model_name,
                        inputs=[inputs],
                        outputs=[outputs],
                    )
                except InferenceServerException as e:
                    logger.error("Triton inference error", error=str(e))
                    raise RuntimeError(f"Triton inference error: {e}")

            # Postprocessing
            with tracer.start_as_current_span("postprocessing"):
                output_data = response.as_numpy("predictions")
                preds = output_data[0]
                top5_idx = np.argsort(preds)[::-1][:5]
                top5_conf = preds[top5_idx]
                results = []
                for idx, conf in zip(top5_idx, top5_conf):
                    results.append(
                        {
                            "class_id": int(idx),
                            "class_name": imagenet_class_index[str(idx)][1],
                            "confidence": float(conf),
                        }
                    )

            # Log profiling data
            logger.info(
                "Profiling results",
                model_used=model_name,
            )

            return {
                "model_used": model_name,
                "predictions": results,
            }
