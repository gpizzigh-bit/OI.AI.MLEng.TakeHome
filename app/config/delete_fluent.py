#!/usr/bin/env python3
import json
import logging
import socket

import structlog

# 1) Set up the standard logging so structlog has somewhere to send output
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

# 2) Configure structlog to use that logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()


def test_socket():
    """Quick raw-TCP check before sending JSON."""
    try:
        sock = socket.create_connection(("fluent-bit", 24224), timeout=3)
        print("✅ Socket connect succeeded")
        sock.close()
    except Exception as e:
        print("❌ Socket connect failed:", e)


if __name__ == "__main__":
    # 1️⃣ Sanity-check raw TCP reachability
    test_socket()

    # 2️⃣ Build your structured record
    record = {
        "log_event": "test_event",
        "message": "Hello from structlog over TCP!",
        "custom_field": "example_value",
    }

    # 3️⃣ Serialize to newline-delimited JSON
    payload = json.dumps(record) + "\n"

    # 4️⃣ Send over TCP to Fluent Bit
    try:
        with socket.create_connection(("fluent-bit", 24224), timeout=3) as sock:
            sock.sendall(payload.encode("utf-8"))
        print("✅ JSON payload sent to Fluent Bit")
    except Exception as e:
        print("❌ Failed to send JSON payload:", e)

    # 5️⃣ Also emit locally via structlog
    logger.info("Finished emit attempt", **record)
