FROM grafana/grafana:latest

# Copy provisioning files
COPY ./services/grafana/provisioning /etc/grafana/provisioning

# Copy dashboards to the correct path
# RUN mkdir -p /var/lib/grafana/dashboards
# COPY ./services/grafana/provisioning/dashboards /var/lib/grafana/dashboards

# # Optionally set permissions
# USER root
# RUN chown -R 472:472 /etc/grafana/provisioning /var/lib/grafana/dashboards

# Switch back to the default Grafana user (UID 472)
USER 472
