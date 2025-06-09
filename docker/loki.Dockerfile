FROM grafana/loki:2.9.0

# Create the config directory in the container
RUN mkdir -p /etc/loki

# Copy the Loki config file into the container
COPY ./app/services/loki/loki-local-config.yaml /etc/loki/local-config.yaml
