# Use the official Triton Inference Server base image
FROM nvcr.io/nvidia/tritonserver:25.05-py3

# Set a working directory (optional, /models is fine for Triton)
WORKDIR /models

# Copy your entire model repository into the container image
COPY ./app/services/triton/models /models

# Expose necessary ports for Triton Inference Server
EXPOSE 8000 8001 8002

# Start Triton Inference Server with the preloaded models
CMD ["tritonserver", "--model-repository=/models", "--log-verbose=1"]
