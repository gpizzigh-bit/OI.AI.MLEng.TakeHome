#!/usr/bin/env bash

set -euo pipefail

echo "🚀 Starting Locust load testing webserver using poetry..."

cd /workspaces/OI.AI.MLEng.TakeHome/tests

# The test file
TEST_FILE="async_locust_scale_test.py"

# Check if the file exists
if [[ ! -f "$TEST_FILE" ]]; then
  echo "❌ Locust test file not found: $TEST_FILE"
  exit 1
fi

# Run Locust with Poetry
poetry run locust -f "$TEST_FILE"

# echo "✅ Locust webserver started. Access it at http://localhost:8089."
