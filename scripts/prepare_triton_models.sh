#!/bin/bash

set -e

# Define the base directory for the Triton model repository
MODEL_REPO="/workspaces/OI.AI.MLEng.TakeHome/services/triton/models"

# Determine Poetry environment's Python executable
PYTHON_PATH=$(poetry env info --path)/bin/python

# Create the base directory if it doesn't exist
mkdir -p "$MODEL_REPO"

# if there are models already in the directory, remove them
if [ -d "$MODEL_REPO" ]; then
  echo "Removing existing models in $MODEL_REPO..."
  rm -rf "$MODEL_REPO"/*
else
  echo "Creating model repository directory at $MODEL_REPO..."
fi

# Define an associative array of models and their corresponding input sizes
# Some models are commented out because Triton runing on my personal 16Gb RAM machine
# may not be able to handle them due to memory constraints.
declare -A models
models=(
  ["Xception"]="299 299"
  ["ResNet152V2"]="224 224"
  ["ResNet101V2"]="224 224"
  ["ResNet50V2"]="224 224"
  # ["ResNet152"]="224 224"
  # ["ResNet101"]="224 224"
  # ["ResNet50"]="224 224"
  # ["VGG19"]="224 224"
  # ["VGG16"]="224 224"
)

# Loop through each model
for model_name in "${!models[@]}"; do
  echo "Processing $model_name..."

  # Extract input dimensions
  read -r height width <<< "${models[$model_name]}"

  # Define paths
  model_dir="$MODEL_REPO/$model_name"
  version_dir="$model_dir/1"
  mkdir -p "$version_dir"

  echo "$PYTHON_PATH"
  echo "Using Python executable: $PYTHON_PATH"

  # Use Poetry environment's Python
  "$PYTHON_PATH" - <<END
import tensorflow as tf
from tensorflow.keras.applications import (
    Xception,
    ResNet152V2,
    ResNet101V2,
    ResNet50V2,
    # ResNet152,
    # ResNet101,
    # ResNet50,
    # VGG19,
    # VGG16,
)
import tf2onnx
import numpy as np

# Define model constructors
model_constructors = {
    "Xception": Xception,
    "ResNet152V2": ResNet152V2,
    "ResNet101V2": ResNet101V2,
    "ResNet50V2": ResNet50V2,
    # "ResNet152": ResNet152,
    # "ResNet101": ResNet101,
    # "ResNet50": ResNet50,
    # "VGG19": VGG19,
    # "VGG16": VGG16,
}

# Load the model
model = model_constructors["$model_name"](weights="imagenet")
model.trainable = False

# Use None for dynamic batch dimension in the export spec
input_shape = (None, $height, $width, 3)
spec = (tf.TensorSpec(input_shape, tf.float32, name="input"),)

# Create dummy input with batch size 1 for tracing
dummy_input = tf.random.uniform((1, $height, $width, 3), dtype=tf.float32)

# Convert the model to ONNX
output_path = "$version_dir/model.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, output_path=output_path, opset=13
)
END

echo "➤ Optimizing ONNX model (overwrite model.onnx with optimized version)..."
poetry run python -m onnxruntime.tools.convert_onnx_models_to_ort \
  "$version_dir/model.onnx" \
  --output_dir "$version_dir" \
  --optimization_style Fixed \
  --save_optimized_onnx_model

echo "✔️  Optimization complete."

# Delete intermediate artifacts to save space
rm -f "$version_dir/model.optimized.onnx"
rm -f "$version_dir/model.ort"
rm -f "$version_dir/required_operands.config" 2>/dev/null || true

# Create the config.pbtxt file with correct 4D input shape
  cat > "$model_dir/config.pbtxt" <<EOL
name: "$model_name"
platform: "onnxruntime_onnx"
max_batch_size: 8
input [
  {
    name: "input"
    data_type: TYPE_FP32
    dims: [$height, $width, 3]
  }
]
output [
  {
    name: "predictions"
    data_type: TYPE_FP32
    dims: [1000]
  }
]
dynamic_batching {
  preferred_batch_size: [4, 8]
  max_queue_delay_microseconds: 100
}
EOL

  echo "$model_name is ready."
done

echo "All models have been processed and optimized for Triton!"
