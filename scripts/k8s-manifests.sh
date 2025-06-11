#!/bin/bash

# This script checks for the presence of necessary Kubernetes manifest files
# and creates them if they are missing.

# The base directory for the Kubernetes manifests.
DIR="../k8s"

# An array of required manifest files.
FILES=(
  "namespace.yaml"
  "triton-deployment.yaml"
  "prometheus-deployment.yaml"
  "grafana-deployment.yaml"
  "loki-deployment.yaml"
  "fluent-bit-deployment.yaml"
  "jaeger-deployment.yaml"
  "otel-collector-deployment.yaml"
  "marine-classifier-deployment.yaml"
  "grafana-pvc.yaml"
  "services.yaml"
  "hpa.yaml"
)

# First, ensure the parent directory exists.
if [ ! -d "$DIR" ]; then
  echo "Directory '$DIR' not found. Creating it."
  mkdir -p "$DIR"
fi

# Loop through the list of files.
for FILE in "${FILES[@]}"; do
  # The full path to the file.
  FILE_PATH="$DIR/$FILE"

  # Check if the file already exists.
  if [ ! -f "$FILE_PATH" ]; then
    # If the file does not exist, create it.
    echo "File '$FILE_PATH' not found. Creating it."
    touch "$FILE_PATH"
  else
    # If the file already exists, do nothing.
    echo "File '$FILE_PATH' already exists."
  fi
done

echo "File check complete. All necessary manifest files are present."
