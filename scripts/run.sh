#!/usr/bin/env bash

set -euo pipefail

echo "🚀 Starting Marine Classifier API Service..."

# Check if Docker is installed
check_docker_installed() {
  if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker before running this script."
    exit 1
  fi
}

# Check if Docker is running
check_docker_running() {
  if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop or your Docker service."
    exit 1
  fi
}

# Start the maestro container
start_maestro() {
  echo "🔧 Rebuilding and starting the maestro container..."

  # Build the image
  docker compose -f ../docker/maestro-compose.yml build maestro

  # Start maestro with a passive command (not demo.sh directly)
  docker compose -f ../docker/maestro-compose.yml up -d maestro

  echo "✅ Maestro container is up and running (detached mode)."
}

# Attach the current terminal to the maestro container
attach_to_maestro() {
  echo "🔗 Attaching your terminal to the maestro container..."
  docker attach maestro
  # docker exec -it maestro bash
}

run_demo_interactive() {
  echo "📡 Launching interactive deployment script inside maestro..."
  docker exec -it maestro bash -c "cd /workspaces/OI.AI.MLEng.TakeHome && bash scripts/demo.sh"
}

# Main script execution
check_docker_installed
check_docker_running
start_maestro
# attach_to_maestro
run_demo_interactive

echo "🎉 Detached from maestro. Goodbye!"
