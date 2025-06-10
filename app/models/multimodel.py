import asyncio
import concurrent.futures
import io
import json
import os
import threading
from functools import partial

import numpy as np
import psutil
import structlog
import tensorflow as tf
from opentelemetry import trace
from PIL import Image
from tensorflow.keras.applications import (
    VGG16,
    VGG19,
    ResNet50,
    ResNet50V2,
    ResNet101,
    ResNet101V2,
    ResNet152,
    ResNet152V2,
    Xception,
    resnet50,
    resnet_v2,
    vgg16,
    vgg19,
    xception,
)

tracer = trace.get_tracer(__name__)


LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
logger = structlog.get_logger()
getattr(logger, LOG_LEVEL, logger.info)("Logger initialized", log_level=LOG_LEVEL)

THREADPOOL_SIZE = int(os.getenv("THREADPOOL_SIZE", "4"))
threadpool_executor = concurrent.futures.ThreadPoolExecutor(max_workers=THREADPOOL_SIZE)

if os.getenv("TF_FORCE_GPU_ALLOW_GROWTH", "false").lower() == "true":
    gpus = tf.config.experimental.list_physical_devices("GPU")
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)


class ModelManager:
    """
    A singleton‐style registry for multiple ImageNet‐pretrained Keras models.
    - At startup, you can call `ModelManager.load_all_models()` to pre‐load each backbone.
    - classify_image(...) is now async: it picks a model, preprocesses, then dispatches
      model.predict(...) into a ThreadPool, so the event loop is never blocked.
    - clear() will clear all models from memory when the program terminates.
    """

    # -----------------------------------------------------------
    # 1) “CPU load → model name” mapping: thresholds must be in ascending order.
    #    If CPU ≤ threshold → pick that model. CPU is measured as a fraction (0.0–1.0).
    # -----------------------------------------------------------
    cpu_to_model_env = os.getenv("CPU_TO_MODEL")
    if cpu_to_model_env:
        try:
            # Try JSON first, fallback to colon/comma format
            if cpu_to_model_env.strip().startswith("["):
                CPU_TO_MODEL = json.loads(cpu_to_model_env)
            else:
                # Format: "0.30:ResNet152V2,0.60:ResNet50V2,0.85:ResNet101V2,1.00:ResNet50"
                CPU_TO_MODEL = [
                    (float(pair.split(":")[0]), pair.split(":")[1])
                    for pair in cpu_to_model_env.split(",")
                ]
        except Exception as e:
            logger.error(
                "Failed to parse CPU_TO_MODEL env var, using default.", error=str(e)
            )
            CPU_TO_MODEL = [
                (0.30, "ResNet152V2"),
                (0.60, "ResNet50V2"),
                (0.85, "ResNet101V2"),
                (1.00, "ResNet50"),
            ]
    else:
        CPU_TO_MODEL = [
            (0.30, "ResNet152V2"),
            (0.60, "ResNet50V2"),
            (0.85, "ResNet101V2"),
            (1.00, "ResNet50"),
        ]

    # -----------------------------------------------------------
    # 2) For each model name, we store:
    #    - the Keras “constructor” (e.g. ResNet50V2)
    #    - the preprocess_input function
    #    - the decode_predictions function
    #    - the expected input size (height, width)
    # -----------------------------------------------------------
    MODEL_INFO = {
        "Xception": {
            "constructor": Xception,
            "preprocess": xception.preprocess_input,
            "decode": xception.decode_predictions,
            "input_size": (299, 299),
        },
        "ResNet152V2": {
            "constructor": ResNet152V2,
            "preprocess": resnet_v2.preprocess_input,
            "decode": resnet_v2.decode_predictions,
            "input_size": (224, 224),
        },
        "ResNet101V2": {
            "constructor": ResNet101V2,
            "preprocess": resnet_v2.preprocess_input,
            "decode": resnet_v2.decode_predictions,
            "input_size": (224, 224),
        },
        "ResNet50V2": {
            "constructor": ResNet50V2,
            "preprocess": resnet_v2.preprocess_input,
            "decode": resnet_v2.decode_predictions,
            "input_size": (224, 224),
        },
        "ResNet152": {
            "constructor": ResNet152,
            "preprocess": resnet50.preprocess_input,
            "decode": resnet50.decode_predictions,
            "input_size": (224, 224),
        },
        "ResNet101": {
            "constructor": ResNet101,
            "preprocess": resnet50.preprocess_input,
            "decode": resnet50.decode_predictions,
            "input_size": (224, 224),
        },
        "ResNet50": {
            "constructor": ResNet50,
            "preprocess": resnet50.preprocess_input,
            "decode": resnet50.decode_predictions,
            "input_size": (224, 224),
        },
        "VGG19": {
            "constructor": VGG19,
            "preprocess": vgg19.preprocess_input,
            "decode": vgg19.decode_predictions,
            "input_size": (224, 224),
        },
        "VGG16": {
            "constructor": VGG16,
            "preprocess": vgg16.preprocess_input,
            "decode": vgg16.decode_predictions,
            "input_size": (224, 224),
        },
    }

    # -----------------------------------------------------------
    # 3) Internal registry for loaded models; guarded by a threading.Lock
    # -----------------------------------------------------------
    _models: dict = {}
    _lock = threading.Lock()

    @classmethod
    def _load_model(cls, model_name: str) -> tf.keras.Model:
        """
        Instantiate and return a Keras model for `model_name`, using
        weights="imagenet". Called inside a lock to ensure each backbone
        is only loaded once.
        """
        info = cls.MODEL_INFO.get(model_name)
        if info is None:
            raise ValueError(f"ModelManager: Unknown model_name '{model_name}'")

        constructor = info["constructor"]
        model = constructor(weights="imagenet")
        return model

    @staticmethod
    def is_ready():
        # Check if all models are loaded and ready
        return all(model is not None for model in ModelManager._models.values())

    @classmethod
    def get_model(cls, model_name: str) -> tf.keras.Model:
        """
        Thread-safe lazy‐loading. If `model_name` is not yet in _models,
        acquire the lock, load it, store it, then return. Otherwise return
        the already-loaded model.
        """
        if model_name not in cls._models:
            with cls._lock:
                if model_name not in cls._models:
                    cls._models[model_name] = cls._load_model(model_name)
        return cls._models[model_name]

    @classmethod
    def load_all_models(cls) -> None:
        """
        Force-load every model named in CPU_TO_MODEL into memory. Call this
        once at program startup (e.g. in FastAPI’s startup event) so that
        classify_image(...) never has to wait on a first-time load.
        """
        model_names = {model_name for _, model_name in cls.CPU_TO_MODEL}
        for name in model_names:
            cls.get_model(name)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all loaded models from RAM and reset the Keras session.
        Call this when the program is terminating.
        """
        with cls._lock:
            cls._models.clear()
        tf.keras.backend.clear_session()

    @classmethod
    def _choose_model_by_cpu(cls) -> str:
        """
        Sample current CPU usage (non-blocking) and return the first
        model_name whose threshold ≥ cpu_pct.
        """
        cpu_pct = psutil.cpu_percent(interval=None) / 100.0
        logger.info("Current CPU usage", cpu_pct=cpu_pct)

        for threshold, model_name in cls.CPU_TO_MODEL:
            if cpu_pct <= threshold:
                return model_name

        return cls.CPU_TO_MODEL[-1][1]

    @classmethod
    async def classify_image(cls, image_data: bytes) -> dict:
        """
        Async version of classify_image:
          1) Decide which model to use based on current CPU load.
          2) Retrieve that model (already pre-loaded via load_all_models()).
          3) Preprocess `image_data`.
          4) Dispatch model.predict(...) into a ThreadPool so the event loop is never blocked.
          5) Decode top-5 predictions.
          6) Return a dict:
                {
                  "model_used": <model_name>,
                  "predictions": [
                      {"class_id": ..., "class_name": ..., "confidence": ...},
                      ...
                  ]
                }
        """
        with tracer.start_as_current_span("modelmanager_classify_image") as span:
            # 1) Pick model by CPU
            with tracer.start_as_current_span("model_selection") as selection_span:
                chosen_model_name = cls._choose_model_by_cpu()
                selection_span.set_attribute("model.name", chosen_model_name)
                # Also attach to parent span for higher-level context
                span.set_attribute("model.name", chosen_model_name)

            # 2) Retrieve the model
            with tracer.start_as_current_span("model_retrieval"):
                model = cls.get_model(chosen_model_name)
                info = cls.MODEL_INFO[chosen_model_name]
                preprocess_fn = info["preprocess"]
                decode_fn = info["decode"]
                input_h, input_w = info["input_size"]

            # 3) Preprocessing
            with tracer.start_as_current_span("preprocessing"):
                try:
                    img = Image.open(io.BytesIO(image_data)).convert("RGB")
                except Exception as e:
                    raise ValueError(f"Could not decode image bytes: {e}")

                img = img.resize((input_w, input_h))
                x = np.asarray(img, dtype=np.float32)
                x = np.expand_dims(x, axis=0)
                x = preprocess_fn(x)

            # 4) Inference (inside threadpool!)
            with tracer.start_as_current_span("inference_call"):
                loop = asyncio.get_running_loop()
                preds = await loop.run_in_executor(
                    threadpool_executor,  # Use the custom executor
                    partial(model.predict, x),  # Pass the model's predict function
                )

            # 5) Postprocessing
            with tracer.start_as_current_span("postprocessing"):
                decoded = decode_fn(preds, top=5)[0]
                results = []
                for class_id, class_name, score in decoded:
                    results.append(
                        {
                            "class_id": class_id,
                            "class_name": class_name,
                            "confidence": float(score),
                        }
                    )

                # Optionally attach top prediction’s confidence
                if results:
                    span.set_attribute(
                        "top_prediction.confidence", results[0]["confidence"]
                    )

            return {
                "model_used": chosen_model_name,
                "predictions": results,
            }
