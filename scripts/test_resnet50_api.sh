#!/usr/bin/env bash

set -uo pipefail  # No 'e' to avoid exit on first error

IMAGES_DIR="tests/images"

echo "🖼️ Available images for testing:"
ls "$IMAGES_DIR" || echo "⚠️ No images found."

echo
read -rp "Enter the image filename to use (e.g., whale.jpg): " IMAGE_NAME

FILE_PATH="$IMAGES_DIR/$IMAGE_NAME"

if [[ ! -f "$FILE_PATH" ]]; then
  echo "❌ File not found: $FILE_PATH"
  exit 1
fi

ENDPOINT="http://marine_classifier:29000/api/v1/predict"

echo "🚀 Sending $IMAGE_NAME to $ENDPOINT ..."

RESPONSE_FILE="response.json"

# Use curl without -s for full error output
# Capture HTTP status separately
HTTP_STATUS=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
  -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@$FILE_PATH" \
  "$ENDPOINT" 2>&1)

CURL_EXIT_CODE=$?

echo
echo "🌟 Response:"
if [[ -f "$RESPONSE_FILE" ]]; then
  cat "$RESPONSE_FILE"
else
  echo "⚠️ No response file created."
fi

echo
echo "🔎 HTTP Status or Error Message: $HTTP_STATUS"

if [[ $CURL_EXIT_CODE -ne 0 ]]; then
  echo "❌ curl command failed with exit code $CURL_EXIT_CODE"
fi

rm -f "$RESPONSE_FILE"

exit 0
