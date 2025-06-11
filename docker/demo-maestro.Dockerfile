# Use a slim Python image as the base
FROM python:3.12-slim-bullseye

# Arguments for the user setup
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create non-root user and install required tools
RUN groupadd --gid $USER_GID $USERNAME \
 && useradd -m --uid $USER_UID --gid $USER_GID -s /bin/bash $USERNAME \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      apt-transport-https \
      ca-certificates \
      curl \
      gnupg \
      lsb-release \
      sudo

# Add Docker's official GPG key
RUN install -m 0755 -d /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
 && chmod a+r /etc/apt/keyrings/docker.asc

# Add the Docker repository to APT sources
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
    > /etc/apt/sources.list.d/docker.list

# Update and install Docker CLI, containerd, Buildx, and Compose plugin
RUN apt-get update \
 && apt-get install -y \
      docker-ce \
      docker-ce-cli \
      containerd.io \
      docker-buildx-plugin \
      docker-compose-plugin \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Add the user to the docker group
RUN getent group docker || groupadd docker \
    && usermod -aG docker $USERNAME

# Allow passwordless sudo for the user
RUN echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nopasswd \
    && chmod 0440 /etc/sudoers.d/nopasswd

# Set the working directory
WORKDIR /workspaces/OI.AI.MLEng.TakeHome

# Set PYTHONPATH for the workspace
ENV PYTHONPATH="/workspaces/OI.AI.MLEng.TakeHome"

# Copy Poetry files and install dependencies
COPY pyproject.toml poetry.lock /workspaces/OI.AI.MLEng.TakeHome/
# Uncomment and adjust if you want Poetry installed:
RUN pip install --no-cache-dir poetry
#     && poetry config virtualenvs.create true \
#     && poetry install

# Copy the rest of the project code
COPY .. /workspaces/OI.AI.MLEng.TakeHome/

# Fix ownership for the workspace
RUN chown -R $USERNAME:$USERNAME /workspaces/OI.AI.MLEng.TakeHome

# Switch to the non-root user
USER $USERNAME

#expose ports fro locust

EXPOSE 8089

# Command to keep the container running (replace with your actual command)
CMD [ "sleep", "infinity" ]
