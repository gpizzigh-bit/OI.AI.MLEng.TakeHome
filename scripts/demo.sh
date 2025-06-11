#!/usr/bin/env bash

set -euo pipefail

echo "------------------------------------------------------------------"
echo "🌊 Welcome to the Marine Classifier API Deployment Demo!"
echo "------------------------------------------------------------------"

echo "Downloading and preparing the project files..."

sudo chown -R $(whoami):$(whoami) /workspaces


echo "🔧 Checking and setting up the Poetry environment..."
cd /workspaces/OI.AI.MLEng.TakeHome
if ! poetry env info --path &>/dev/null; then
  echo "⚠️ Poetry environment not found! Running 'poetry install' to set it up..."
  poetry install
  echo "✅ Poetry environment created!"
else
  echo "✅ Poetry environment already exists."
fi

cd /workspaces/OI.AI.MLEng.TakeHome/scripts

echo "Downloading testing images..."
# Download testing images
bash get_test_images.sh
echo "✅ Testing images downloaded."

echo "Downloading models data..."
bash prepare_triton_models.sh || echo "⚠️ prepare_triton_models.sh exited with non-zero status"
echo "✅ Models data downloaded."

# go back to the project root
cd /workspaces/OI.AI.MLEng.TakeHome

# Deployment option selection loop
while true; do
  echo "🔧 Please choose a deployment option:"
  echo "1) Docker Compose"
  echo "2) Kubernetes"

  read -rp "Enter 1 or 2: " DEPLOY_OPTION

  case "$DEPLOY_OPTION" in
    1)
      echo "🐳 You selected Docker Compose."
      echo "🔧 Starting services with Docker Compose..."

      # Launch the services
      bash scripts/setup-infra.sh

      #add the maestro container to the skynet network
     sudo docker network connect skynet maestro

      echo "✅ Docker Compose services are running."
      break  # Exit the loop on successful selection
      ;;
    2)
      echo "☸️ You selected Kubernetes."
      echo "⚠️ Note: Kubernetes deployment is partially implemented and untested!"

      # Navigate to the k8s directory
      cd /workspaces/OI.AI.MLEng.TakeHome/k8s

      # Apply Kubernetes manifests
      kubectl apply -f .

      echo "✅ Kubernetes manifests applied."
      echo "ℹ️ Use 'kubectl get pods' to check status."
      break  # Exit the loop on successful selection
      ;;
    *)
      echo "❌ Invalid selection. Please choose 1 or 2."
      echo "------------------------------------------"
      ;;
  esac
done

# Testing loop
while true; do
  echo "🔎 Testing readiness endpoint manually... Please wait as this can take some time..."

  if ! curl -s http://marine_classifier:29000/readiness; then
    echo "⚠️ Api not ready yet. Retrying in 5 seconds..."
    sleep 5
    continue
  fi

  READINESS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://marine_classifier:29000/readiness || echo "000")

  if [[ "$READINESS_STATUS" -ne 200 ]]; then
    echo "⚠️ API is not ready yet. Readiness endpoint returned HTTP $READINESS_STATUS"
    echo "🔄 Retrying in 5 seconds..."
    sleep 5
    continue  # Skip showing the menu and retry
  fi

  echo "✅ API is ready!"
  echo
  echo "🌟 Please choose an API testing option:"
  echo "1) Test simple ResNet50 predict API"
  echo "2) Test CPU load balancing smart API"
  echo "3) Test Triton inference service API"
  echo "4) Open a Locust webserver to test multiple users and run asynchronous calls"
  echo "q) Quit"

  read -rp "Enter 1, 2, 3, 4 or q: " TEST_OPTION

  case "$TEST_OPTION" in
    1)
      echo "🧪 Running ResNet50 predict API test..."
      if ! bash scripts/test_resnet50_api.sh; then
        echo "⚠️ Sub-script failed, returning to menu..."
      fi
      echo "✅ ResNet50 predict API test completed."
      ;;
    2)
      echo "🧪 Running CPU load balancing smart API test..."
      if ! bash scripts/test_cpu_load_balancing.sh; then
        echo "⚠️ Sub-script failed, returning to menu..."
      fi
      echo "✅ CPU load balancing smart API test completed."
      ;;
    3)
      echo "🧪 Running Triton inference service API test..."
      if ! bash scripts/test_triton_api.sh; then
        echo "⚠️ Sub-script failed, returning to menu..."
      fi
      echo "✅ Triton inference service API test completed."
      ;;
    4)
      echo "🧪 Starting Locust webserver for load testing..."
      if ! bash scripts/test_locust.sh; then
        echo "⚠️ Sub-script failed, returning to menu..."
      fi
      echo "✅ Locust webserver started. Open http://localhost:8089 to interact."
      ;;
    q)
      echo "👋 Exiting the testing loop. Goodbye!"
      break
      ;;
    *)
      echo "❌ Invalid selection. Please choose 1, 2, 3, 4 or q."
      ;;
  esac
done

# Prompt to clean up resources
read -rp "🧹 Do you want to stop services and clean up resources? (y/n): " CLEANUP_CHOICE
if [[ "$CLEANUP_CHOICE" == "y" || "$CLEANUP_CHOICE" == "Y" ]]; then
  bash scripts/stop_and_clean.sh
else
  echo "⚠️ Skipping cleanup. Resources will remain running."
fi

echo "Thank you for using the Marine Classifier API Deployment Demo!"
echo "------------------------------------------------------------------"
echo "🌊 Have a great day! 🐠"
echo "------------------------------------------------------------------"

sudo docker compose -f docker/maestro-compose.yml down
