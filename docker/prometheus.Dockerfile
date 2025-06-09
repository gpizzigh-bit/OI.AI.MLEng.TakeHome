FROM prom/prometheus:latest

COPY ./services/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
