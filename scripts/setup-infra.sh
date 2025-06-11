#!/usr/bin/env bash
set -e

# Network name
NETWORK_NAME="skynet"

# Check if the network exists
if ! sudo docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
  echo "Creating network: ${NETWORK_NAME}"
  sudo docker network create ${NETWORK_NAME}
else
  echo "Network ${NETWORK_NAME} already exists"
fi

# Navigate to the docker folder
cd /workspaces/OI.AI.MLEng.TakeHome/docker

# Run docker compose up
echo "Running docker compose to raise the infrastructure..."
sudo docker compose up -d --build

echo "Infrastructure started successfully!"
