FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy only dependency files first for caching
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies with virtual env

RUN poetry config virtualenvs.create true && \
    poetry install --no-interaction --no-ansi --only main

# Copy app code
COPY ./app ./app


# Expose port
EXPOSE 29000

# Run the API using the main.py script
# CMD ["poetry", "run", "python3", "app/main.py"]
CMD ["/bin/bash", "-c", "poetry run python3 app/main.py; while true; do sleep 1000; done"]
# Note: The CMD command assumes that the main.py script is the entry point for your application.
