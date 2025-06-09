#!/bin/bash

# Set the project root directory as one level above the scripts folder
PROJECT_ROOT="../"

# Navigate to the project root directory
cd "$PROJECT_ROOT" || exit

# Create the directory structure
mkdir -p app/{api,core,models}
mkdir -p services # Microservices directory
mkdir -p app/api/v1 # Versioned API directory more can be added later
mkdir -p tests
mkdir -p docker      # Dockerfiles and Compose configurations
mkdir -p kubernetes  # Kubernetes manifests
mkdir -p docs       # Documentation
mkdir -p .github/workflows # GitHub Actions workflows


# Create essential Python files
touch app/__init__.py
touch app/main.py

# Create essential project files
touch docker/Dockerfile
touch docker/docker-compose.yml
touch .dockerignore
touch .gitignore
touch README.md

echo "✅ Project structure created in '$PROJECT_ROOT'"

# Check if poetry is installed
if command -v poetry &> /dev/null; then
    echo "🎵 Poetry is installed."

    # Disable virtual environments for container-based development
    poetry config virtualenvs.create false

    # Check if pyproject.toml already exists
    if [ -f pyproject.toml ]; then
        echo "🔍 pyproject.toml already exists. Skipping poetry initialization."
    else
        echo "📝 Initializing poetry project interactively..."
        poetry init
    fi

    echo "✅ Poetry configuration complete."
else
    echo "❌ Poetry is not installed. Please install it to manage dependencies."
fi
