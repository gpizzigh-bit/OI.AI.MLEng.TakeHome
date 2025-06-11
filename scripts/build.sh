#!/bin/bash

# Script to build Docker images for the application components

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Error Handling Trap ---
handle_error() {
    local exit_code=$?
    local last_command=${BASH_COMMAND}
    echo "❌ ERROR: Command failed with exit code $exit_code."
    echo "❌ Failed command: '$last_command'"
    echo "❌ Image build aborted. Please review the error above."
    exit $exit_code
}
trap 'handle_error' ERR

echo "⚙️ Starting Docker image build process..."
echo "--------------------------------------------------"

# Define the root directory of your project (assuming script is in scripts/)
# This makes the project root the build context, allowing Dockerfiles to copy from anywhere in the project.
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
DOCKERFILES_DIR="${PROJECT_ROOT}/docker" # Directory containing your Dockerfiles

# --- Image Tag Configuration ---
# You can set an IMAGE_TAG environment variable before running the script, e.g.:
# export IMAGE_TAG=v1.0.0
# If IMAGE_TAG is not set, it defaults to 'latest'.
IMAGE_TAG=${IMAGE_TAG:-latest}
IMAGE_PREFIX="prod-" # Desired prefix for your production images

echo "Building images with tag: ${IMAGE_TAG}"
echo "Image prefix: ${IMAGE_PREFIX}"
echo "Build Context: ${PROJECT_ROOT}"
echo "--------------------------------------------------"

# Array of Dockerfile base names (without .Dockerfile extension)
# Exclude 'docker-compose' and 'maestro' as per your request
declare -a dockerfiles_to_build=(
    "fluent-bit"
    "grafana"
    "loki"
    "marine"
    "otel"
    "prometheus"
    "triton"
)

# Loop through each Dockerfile base name and build the corresponding image
for df_basename in "${dockerfiles_to_build[@]}"; do
    DOCKERFILE_PATH="${DOCKERFILES_DIR}/${df_basename}.Dockerfile"
    IMAGE_NAME="${IMAGE_PREFIX}${df_basename}"
    FULL_IMAGE_TAG="${IMAGE_NAME}:${IMAGE_TAG}"

    if [ -f "$DOCKERFILE_PATH" ]; then
        echo "Building image: ${FULL_IMAGE_TAG}"
        echo "  Using Dockerfile: ${DOCKERFILE_PATH}"
        echo "  With build context: ${PROJECT_ROOT}"

        # Build the Docker image
        sudo docker build \
            -f "${DOCKERFILE_PATH}" \
            -t "${FULL_IMAGE_TAG}" \
            "${PROJECT_ROOT}" # Use project root as the build context

        echo "Successfully built: ${FULL_IMAGE_TAG}"
        echo "--------------------------------------------------"
    else
        echo "⚠️ Warning: Dockerfile not found, skipping: ${DOCKERFILE_PATH}"
        echo "--------------------------------------------------"
    fi
done

echo "✅ All specified Docker images built successfully!"
echo ""
echo "You can view your new images with: docker images '${IMAGE_PREFIX}*'"
