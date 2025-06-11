#!/bin/bash

# Script to deploy Kubernetes manifests using kubectl

# Exit immediately if a command exits with a non-zero status.
# If a command fails, the script will stop and the ERR trap will be activated.
set -e

# --- Error Handling Trap ---
# This function will be executed whenever a command exits with a non-zero status (due to 'set -e')
# It provides more context about which command failed.
handle_error() {
    local exit_code=$?
    local last_command=${BASH_COMMAND}
    echo "❌ ERROR: Command failed with exit code $exit_code."
    echo "❌ Failed command: '$last_command'"
    echo "❌ Deployment aborted. Please review the error above."
    exit $exit_code
}

# Set the trap: call handle_error function on any ERR (error) signal
trap 'handle_error' ERR

echo "🚀 Starting Kubernetes manifest deployment..."

# Define the directory where your k8s manifests are located
MANIFESTS_DIR="k8s"
NAMESPACE_FILE="${MANIFESTS_DIR}/namespace.yaml" # Define path to namespace file

# Check if the manifests directory exists
if [ ! -d "$MANIFESTS_DIR" ]; then
    echo "❌ Error: Manifests directory '$MANIFESTS_DIR' not found."
    echo "❌ Please ensure your Kubernetes manifest files are in this directory relative to the script."
    exit 1
fi

echo "Deploying manifests from: $MANIFESTS_DIR"
echo "--------------------------------------------------"

# --- Extract Namespace from namespace.yaml ---
NAMESPACE=""
if [ -f "$NAMESPACE_FILE" ]; then
    echo "Attempting to extract namespace from $NAMESPACE_FILE..."
    # Use yq to parse the namespace name from the metadata.name field
    # This assumes namespace.yaml contains a single Namespace kind definition
    NAMESPACE=$(yq '.metadata.name' "$NAMESPACE_FILE")

    if [ -z "$NAMESPACE" ]; then
        echo "⚠️ Warning: Could not extract namespace name using 'yq .metadata.name' from $NAMESPACE_FILE."
        echo "⚠️ The 'namespace.yaml' might not contain a Namespace resource at the root or 'metadata.name' is missing."
        echo "⚠️ Commands will use '<your-namespace>' placeholder."
        NAMESPACE="<your-namespace>" # Fallback if yq fails or name is empty
    else
        echo "Detected Namespace: $NAMESPACE"
    fi
else
    echo "⚠️ Warning: namespace.yaml not found at $NAMESPACE_FILE."
    echo "⚠️ Commands will use '<your-namespace>' placeholder."
    NAMESPACE="<your-namespace>" # Fallback if file not found
fi
echo "--------------------------------------------------"

# --- Deployment Order ---
# This order is crucial for dependencies:
# 1. Namespace (if defined separately)
# 2. Persistent Volume Claims (PVCs)
# 3. Core Deployments (components without strict cross-component dependencies, EXCEPT Triton)
# 4. Triton Deployment (specifically handled due to Marine dependency)
# 5. **Wait for Triton to be Ready**
# 6. Marine Classifier Deployment (depends on Triton)
# 7. Services (expose deployments - applied after all relevant deployments)
# 8. Horizontal Pod Autoscalers (HPAs)

# 1. Apply Namespace (if it exists)
if [ -f "${MANIFESTS_DIR}/namespace.yaml" ]; then
    echo "Applying: ${MANIFESTS_DIR}/namespace.yaml"
    kubectl apply -f "${MANIFESTS_DIR}/namespace.yaml"
    echo ""
fi

# 2. Apply PVCs
echo "Applying Persistent Volume Claims..."
for pvc_manifest in "${MANIFESTS_DIR}"/*-pvc.yaml; do
    if [ -f "$pvc_manifest" ]; then
        echo "Applying: $pvc_manifest"
        kubectl apply -f "$pvc_manifest"
    fi
done
echo ""

# 2.5. Apply ConfigMaps
echo "Applying ConfigMaps..."
for configmap_manifest in "${MANIFESTS_DIR}"/*-configmap.yaml; do
    if [ -f "$configmap_manifest" ]; then
        echo "Applying: $configmap_manifest"
        kubectl apply -f "$configmap_manifest"
    fi
done
echo ""

# 3. Apply core deployments (all except triton and marine-classifier)
# Adjust this list based on your actual files and their dependencies.
echo "Applying core deployments (excluding Triton and Marine Classifier)..."
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
        echo "Applying: $FILE_PATH"
        kubectl apply -f "$FILE_PATH"
    else
        echo "⚠️ Warning: Deployment file not found, skipping: $FILE_PATH"
    fi
    echo ""
done

# 4. Apply Triton Deployment
TRITON_DEPLOYMENT_FILE="${MANIFESTS_DIR}/triton-deployment.yaml"
if [ -f "$TRITON_DEPLOYMENT_FILE" ]; then
    echo "Applying: $TRITON_DEPLOYMENT_FILE"
    kubectl apply -f "$TRITON_DEPLOYMENT_FILE"
    echo ""

    # 5. Wait for Triton to be Ready
    echo "⏳ Waiting for Triton deployment 'triton' to be ready in namespace '${NAMESPACE}' (timeout 5 minutes)..."
    # Ensure your triton-deployment.yaml has a readinessProbe defined!
    kubectl wait --for=condition=Available deployment/triton -n "${NAMESPACE}" --timeout=300s
    echo "✅ Triton deployment is ready!"
    echo ""
else
    echo "❌ Error: triton-deployment.yaml not found at $TRITON_DEPLOYMENT_FILE. Cannot proceed without Triton."
    exit 1
fi

# 6. Apply Marine Classifier Deployment
MARINE_DEPLOYMENT_FILE="${MANIFESTS_DIR}/marine-classifier-deployment.yaml"
if [ -f "$MARINE_DEPLOYMENT_FILE" ]; then
    echo "Applying: $MARINE_DEPLOYMENT_FILE"
    kubectl apply -f "$MARINE_DEPLOYMENT_FILE"
    echo ""
else
    echo "❌ Error: marine-classifier-deployment.yaml not found at $MARINE_DEPLOYMENT_FILE."
    exit 1
fi

# 7. Apply Services (after all relevant deployments are at least started)
SERVICES_FILE="${MANIFESTS_DIR}/services.yaml"
if [ -f "$SERVICES_FILE" ]; then
    echo "Applying: $SERVICES_FILE"
    kubectl apply -f "$SERVICES_FILE"
    echo ""
else
    echo "⚠️ Warning: services.yaml not found at $SERVICES_FILE. Skipping services."
fi

# 8. Apply HPAs
HPA_FILE="${MANIFESTS_DIR}/hpa.yaml"
if [ -f "$HPA_FILE" ]; then
    echo "Applying: $HPA_FILE"
    kubectl apply -f "$HPA_FILE"
    echo ""
else
    echo "⚠️ Warning: hpa.yaml not found at $HPA_FILE. Skipping HPAs."
fi

echo "--------------------------------------------------"
echo "✅ All specified Kubernetes manifests applied successfully!"
echo ""
echo "You can check the status of your deployments in the '$NAMESPACE' namespace with:"
echo "kubectl get pods -n $NAMESPACE"
echo "kubectl get svc -n $NAMESPACE"
echo "kubectl get hpa -n $NAMESPACE"
