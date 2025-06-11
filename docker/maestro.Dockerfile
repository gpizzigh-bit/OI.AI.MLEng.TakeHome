# Use a slim Python image as the base
FROM python:3.12-slim-bullseye

# ARG for USERNAME, same as default dev container setup
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create a non-root user for development
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y --no-install-recommends apt-transport-https ca-certificates curl gnupg2 sudo\
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Install yq (Go-based) ---
# Download the latest stable yq binary for Linux AMD64
# You can check for the latest version at https://github.com/mikefarah/yq/releases
ENV YQ_VERSION="4.45.4"
RUN curl -sSL "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64" -o /usr/local/bin/yq \
    && chmod +x /usr/local/bin/yq

RUN groupadd docker \
    && usermod -aG docker $USERNAME

RUN echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nopasswd \
    && chmod 0440 /etc/sudoers.d/nopasswd

# Install kubectl using the latest recommended APT method
# Kubernetes 1.33 is currently the latest stable (as of your provided text's release dates)
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.33/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.33/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list \
    && apt-get update \
    && apt-get install -y kubectl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/OI.AI.MLEng.TakeHome

ENV PYTHONPATH="/workspaces/OI.AI.MLEng.TakeHome"

# copy poetry files and install dependencies
COPY pyproject.toml poetry.lock /workspaces/OI.AI.MLEng.TakeHome/
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create true \
    && poetry install

# Copy the rest of the project code
COPY .. /workspaces/OI.AI.MLEng.TakeHome/

# Set the user to the non-root user created earlier
RUN chown -R $USERNAME:$USERNAME /workspaces/OI.AI.MLEng.TakeHome
USER $USERNAME

# With:
CMD [ "sleep", "infinity" ]
