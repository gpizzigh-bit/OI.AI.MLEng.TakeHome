FROM otel/opentelemetry-collector-contrib:latest

COPY ./services/otel/otel-collector-config.yml /etc/otel-collector-config.yaml
