#!/usr/bin/env bash

set -euo pipefail

echo "------------------------------------------------------------------"
echo "🛑 Stopping Marine Classifier API and cleaning up resources..."
echo "------------------------------------------------------------------"

# Navigate to the project root (adjust if needed)
cd /workspaces/OI.AI.MLEng.TakeHome

echo "🔎 Stopping Docker Compose services..."
sudo docker compose -f docker/docker-compose.yml down

echo "✅ Services stopped."

#dettach the maestro container from the skynet network
echo "🔎 Detaching the 'maestro' container from the 'skynet' network..."
if sudo docker network inspect skynet &>/dev/null; then
  if sudo docker network disconnect skynet maestro; then
    echo "✅ 'maestro' container detached from 'skynet' network."
  else
    echo "⚠️ Failed to detach 'maestro' container from 'skynet' network. It may not be connected."
  fi
else
  echo "ℹ️ 'skynet' network does not exist. No detachment needed."
fi

# Clean up the skynet network if it exists
echo "🔎 Checking and removing the 'skynet' network (if it exists)..."
if sudo docker network inspect skynet &>/dev/null; then
  sudo docker network rm skynet
  echo "✅ 'skynet' network removed."
else
  echo "ℹ️ 'skynet' network does not exist. No cleanup needed."
fi

echo "✅ Cleanup completed."
echo "------------------------------------------------------------------"
echo "🌊 Marine Classifier environment is now clean!"
echo "------------------------------------------------------------------"
