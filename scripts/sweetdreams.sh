#!/bin/bash

# Script to take down Kubernetes manifests using kubectl

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Error Handling Trap ---
handle_error() {
    local exit_code=$?
    local last_command=${BASH_COMMAND}
    echo "❌ ERROR: Command failed with exit code $exit_code."
    echo "❌ Failed command: '$last_command'"
    echo "❌ Teardown aborted. Please review the error above."
    exit $exit_code
}

trap 'handle_error' ERR

echo "🛑 Starting Kubernetes manifest teardown..."

# Define the directory where your k8s manifests are located
MANIFESTS_DIR="../k8s"
NAMESPACE_FILE="${MANIFESTS_DIR}/namespace.yaml"

# Extract namespace (same logic as in deploy.sh)
NAMESPACE=""
if [ -f "$NAMESPACE_FILE" ]; then
    echo "Extracting namespace from $NAMESPACE_FILE..."
    NAMESPACE=$(yq '.metadata.name' "$NAMESPACE_FILE")
    if [ -z "$NAMESPACE" ]; then
        echo "⚠️ Could not extract namespace; using '<your-namespace>'."
        NAMESPACE="<your-namespace>"
    else
        echo "Detected Namespace: $NAMESPACE"
    fi
else
    echo "⚠️ namespace.yaml not found. Using '<your-namespace>'."
    NAMESPACE="<your-namespace>"
fi
echo "--------------------------------------------------"

# --- Teardown Order ---
# Reverse of deploy.sh:
# 1. HPAs
# 2. Services
# 3. Marine Classifier Deployment
# 4. Triton Deployment
# 5. Core Deployments
# 6. PVCs
# 7. Namespace

# 1. Delete HPAs
HPA_FILE="${MANIFESTS_DIR}/hpa.yaml"
if [ -f "$HPA_FILE" ]; then
    echo "Deleting HPAs from: $HPA_FILE"
    kubectl delete -f "$HPA_FILE" --ignore-not-found=true
    echo ""
else
    echo "⚠️ hpa.yaml not found at $HPA_FILE. Skipping HPAs."
fi

# 2. Delete Services
SERVICES_FILE="${MANIFESTS_DIR}/services.yaml"
if [ -f "$SERVICES_FILE" ]; then
    echo "Deleting Services from: $SERVICES_FILE"
    kubectl delete -f "$SERVICES_FILE" --ignore-not-found=true
    echo ""
else
    echo "⚠️ services.yaml not found at $SERVICES_FILE. Skipping services."
fi

# 3. Delete Marine Classifier Deployment
MARINE_DEPLOYMENT_FILE="${MANIFESTS_DIR}/marine-classifier-deployment.yaml"
if [ -f "$MARINE_DEPLOYMENT_FILE" ]; then
    echo "Deleting: $MARINE_DEPLOYMENT_FILE"
    kubectl delete -f "$MARINE_DEPLOYMENT_FILE" --ignore-not-found=true
    echo ""
else
    echo "⚠️ marine-classifier-deployment.yaml not found. Skipping."
fi

# 4. Delete Triton Deployment
TRITON_DEPLOYMENT_FILE="${MANIFESTS_DIR}/triton-deployment.yaml"
if [ -f "$TRITON_DEPLOYMENT_FILE" ]; then
    echo "Deleting: $TRITON_DEPLOYMENT_FILE"
    kubectl delete -f "$TRITON_DEPLOYMENT_FILE" --ignore-not-found=true
    echo ""
else
    echo "⚠️ triton-deployment.yaml not found. Skipping."
fi

# 5. Delete core deployments
declare -a core_deployments=(
    "fluent-bit-deployment.yaml"
    "grafana-deployment.yaml"
    "jaeger-deployment.yaml"
    "loki-deployment.yaml"
    "otel-collector-deployment.yaml"
    "prometheus-deployment.yaml"
)
for dep_manifest in "${core_deployments[@]}"; do
    FILE_PATH="${MANIFESTS_DIR}/${dep_manifest}"
    if [ -f "$FILE_PATH" ]; then
        echo "Deleting: $FILE_PATH"
        kubectl delete -f "$FILE_PATH" --ignore-not-found=true
    else
        echo "⚠️ $dep_manifest not found. Skipping."
    fi
    echo ""
done

# 6. Delete PVCs
echo "Deleting Persistent Volume Claims..."
for pvc_manifest in "${MANIFESTS_DIR}"/*-pvc.yaml; do
    if [ -f "$pvc_manifest" ]; then
        echo "Deleting: $pvc_manifest"
        kubectl delete -f "$pvc_manifest" --ignore-not-found=true
    fi
done
echo ""


# 7. Delete ConfigMaps
echo "Deleting ConfigMaps..."
for configmap_manifest in "${MANIFESTS_DIR}"/*-configmap.yaml; do
    if [ -f "$configmap_manifest" ]; then
        echo "Deleting: $configmap_manifest"
        kubectl delete -f "$configmap_manifest" --ignore-not-found=true
    fi
done
echo ""

# 8. Delete Namespace (last, to avoid deleting resources still using it)
if [ -f "$NAMESPACE_FILE" ]; then
    echo "Deleting Namespace: $NAMESPACE_FILE"
    kubectl delete -f "$NAMESPACE_FILE" --ignore-not-found=true
    echo ""
else
    echo "⚠️ namespace.yaml not found. Skipping namespace deletion."
