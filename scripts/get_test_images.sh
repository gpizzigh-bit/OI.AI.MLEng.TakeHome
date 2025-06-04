#!/bin/bash

PROJECT_ROOT="../"

# Navigate to the project root directory
cd "$PROJECT_ROOT" || exit

# Define the target directory
TARGET_DIR="tests/images"

# Create the directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Declare an associative array of marine animals and their image URLs
declare -A animals=(
  ["clownfish"]="https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Black_storm_Clownfish.jpg/640px-Black_storm_Clownfish.jpg"
  ["sea_turtle"]="https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Chelonia_mydas_green_sea_turtle_6.jpg/640px-Chelonia_mydas_green_sea_turtle_6.jpg"
  ["starfish"]="https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Asterias_rubens_375592891.jpg/640px-Asterias_rubens_375592891.jpg"
  ["stingray"]="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Stingray_Eco-Tourism.jpg/640px-Stingray_Eco-Tourism.jpg"
  ["whale"]="https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Baie_de_Gaspe_950626_006a.jpg/640px-Baie_de_Gaspe_950626_006a.jpg"
  ["seahorse"]="https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Sabella_pavonina_-_Hippocampus_hippocampus_-_Porto_Cesareo%2C_Italy_%28DSC2314M%29.jpg/640px-Sabella_pavonina_-_Hippocampus_hippocampus_-_Porto_Cesareo%2C_Italy_%28DSC2314M%29.jpg"
  ["jellyfish"]="https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Jellyfish_%2845634111522%29.jpg/640px-Jellyfish_%2845634111522%29.jpg"
  ["octopus"]="https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Hairy_octopus_%28Octopus_sp.%29_%2842825525344%29.jpg/640px-Hairy_octopus_%28Octopus_sp.%29_%2842825525344%29.jpg"
  ["dolphin"]="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Parc_Asterix_20.jpg/640px-Parc_Asterix_20.jpg"
  ["shark"]="https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"
)

# Iterate over the animals
for animal in "${!animals[@]}"; do
  filename="$TARGET_DIR/${animal}.jpg"
  url="${animals[$animal]}"

  if [ -f "$filename" ]; then
    echo "✅ $animal image already exists. Skipping download."
  else
    echo "⬇️ Downloading $animal image..."
    curl -s -o "$filename" "$url"
    if [ $? -eq 0 ]; then
      echo "✅ Downloaded $animal image successfully."
    else
      echo "❌ Failed to download $animal image."
    fi
  fi
done
