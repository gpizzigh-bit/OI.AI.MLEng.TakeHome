import logging
import os
import socket
import sys

import structlog


class TCPJSONHandler(logging.Handler):
    """
    A logging handler that sends each record as newline-delimited JSON
    to Fluent Bit over a TCP socket.
    """

    def __init__(self, host="fluent-bit", port=24224, timeout=1):
        super().__init__(level=logging.INFO)
        self.host = host
        self.port = port
        self.timeout = timeout

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            if not msg.endswith("\n"):
                msg += "\n"
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                sock.sendall(msg.encode("utf-8"))
        except Exception:
            self.handleError(record)


def configure_logging(log_folder="logs", log_file_name="app.log"):
    """
    Configure structlog + stdlib logging for:
      - File (overwrite each run)
      - Console (stdout)
      - Fluent Bit (raw JSON over TCP)
    """
    # Ensure log folder exists
    os.makedirs(log_folder, exist_ok=True)
    log_file_path = os.path.join(log_folder, log_file_name)

    # File handler
    file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # TCP JSON handler for Fluent Bit
    tcp_handler = TCPJSONHandler(host="fluent-bit", port=24224)
    tcp_handler.setLevel(logging.INFO)
    tcp_handler.setFormatter(logging.Formatter("%(message)s"))

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(tcp_handler)

    # structlog configuration
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_class_logger(class_name: str, log_folder="logs"):
    """
    Creates a dedicated structlog logger for a specific class, writing to its own file
    and sending to Fluent Bit over TCP.
    """
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, f"{class_name}.log")

    # File handler for this class
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # TCP handler for this class
    tcp_handler = TCPJSONHandler(host="fluent-bit", port=24224)
    tcp_handler.setLevel(logging.INFO)
    tcp_handler.setFormatter(logging.Formatter("%(message)s"))

    # Create a separate logger instance
    logger_name = f"{class_name}_logger"
    dedicated_logger = logging.getLogger(logger_name)
    dedicated_logger.setLevel(logging.INFO)
    dedicated_logger.handlers.clear()
    dedicated_logger.addHandler(file_handler)
    dedicated_logger.addHandler(tcp_handler)

    # Wrap with structlog
    return structlog.wrap_logger(
        dedicated_logger,
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
    )
