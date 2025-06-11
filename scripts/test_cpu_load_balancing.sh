#!/usr/bin/env bash

set -euo pipefail

IMAGES_DIR="tests/images"

echo "🖼️ Available images for testing:"
ls "$IMAGES_DIR"

echo
read -rp "Enter the image filename to use (e.g., whale.jpg): " IMAGE_NAME

FILE_PATH="$IMAGES_DIR/$IMAGE_NAME"

if [[ ! -f "$FILE_PATH" ]]; then
  echo "❌ File not found: $FILE_PATH"
  exit 1
fi

ENDPOINT="http://marine_classifier:29000/api/v1/smart_predict"

echo "🚀 Sending $IMAGE_NAME to $ENDPOINT ..."
RESPONSE_FILE="response.json"

HTTP_STATUS=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
  -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@$FILE_PATH" \
  "$ENDPOINT")

echo
echo "🌟 Response:"
cat "$RESPONSE_FILE"
echo
echo "🔎 HTTP Status: $HTTP_STATUS"

rm -f "$RESPONSE_FILE"
