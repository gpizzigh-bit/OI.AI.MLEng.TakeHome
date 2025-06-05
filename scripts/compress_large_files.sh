#!/bin/bash
set -e

# Set size threshold to 500 KB
THRESHOLD=$((500 * 1024))

for file in "$@"; do
  if [ -f "$file" ]; then
    size=$(stat -c%s "$file")
    if [ "$size" -gt "$THRESHOLD" ]; then
      gzip -kf "$file"
      echo "Compressed $file to $file.gz"
    fi
  fi
done
