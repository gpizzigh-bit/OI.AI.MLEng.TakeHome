import io
import json
import threading
import time

import numpy as np
import psutil
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from tritonclient.http import (
    InferenceServerClient,
    InferenceServerException,
    InferInput,
    InferRequestedOutput,
)

from app.config.logger import get_class_logger

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
        # Profiling start
        start_total = time.time()
        model_name = self._choose_model_by_cpu()
        info = self.MODEL_INFO[model_name]
        input_h, input_w = info["input_size"]
        preprocess_fn = info["preprocess"]

        # Step 1: Load and preprocess image
        start_preprocess = time.time()
        try:
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            logger.error("Image decode error", error=str(e))
            raise ValueError(f"Could not decode image bytes: {e}")

        img = img.resize((input_w, input_h))
        x = np.asarray(img, dtype=np.float32)
        x = np.expand_dims(x, axis=0)  # (1, H, W, 3)
        x = preprocess_fn(x)
        preprocess_time = time.time() - start_preprocess

        # Step 2: Health check
        start_health = time.time()
        try:
            is_ready = await run_in_threadpool(self.client.is_model_ready, model_name)
            if not is_ready:
                raise RuntimeError(f"Triton model '{model_name}' is not ready.")
        except InferenceServerException as e:
            logger.error("Triton health-check error", error=str(e))
            raise RuntimeError(f"Triton health-check failed: {e}")
        health_time = time.time() - start_health

        # Step 3: Inference
        start_infer = time.time()
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
        infer_time = time.time() - start_infer

        # Step 4: Postprocess
        start_post = time.time()
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
        postprocess_time = time.time() - start_post

        # Total time
        total_time = time.time() - start_total

        # Log profiling data
        logger.info(
            "Profiling results",
            model_used=model_name,
            total_time=f"{total_time:.4f}s",
            preprocess_time=f"{preprocess_time:.4f}s",
            healthcheck_time=f"{health_time:.4f}s",
            inference_time=f"{infer_time:.4f}s",
            postprocess_time=f"{postprocess_time:.4f}s",
        )

        return {
            "model_used": model_name,
            "predictions": results,
        }
