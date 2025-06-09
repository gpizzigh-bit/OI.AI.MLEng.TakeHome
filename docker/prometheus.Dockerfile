FROM prom/prometheus:latest

COPY ./app/services/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
