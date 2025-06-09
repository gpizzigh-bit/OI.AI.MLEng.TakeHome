FROM fluent/fluent-bit:latest

COPY ./services/fluent-bit/fluent-bit.conf /fluent-bit/etc/fluent-bit.conf
