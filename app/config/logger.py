import logging
import os
import sys

import structlog


def configure_logging(log_folder="logs", log_file_name="app.log"):
    """
    Configure structlog to log to both console and a log file.
    - log_folder: folder for logs
    - log_file_name: name of the log file (e.g., 'TritonMultiModel.log')
    """

    # Ensure log folder exists
    os.makedirs(log_folder, exist_ok=True)

    # Build log file path
    log_file_path = os.path.join(log_folder, log_file_name)

    # File handler
    file_handler = logging.FileHandler(
        log_file_path, mode="w", encoding="utf-8"
    )  # write mode so it overwrites the file and we don't accumulate logs
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    file_formatter = logging.Formatter("%(message)s")
    console_formatter = logging.Formatter("%(message)s")

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # structlog config
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
    Creates a dedicated structlog logger for a specific class, writing to its own file.
    """
    import os

    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, f"{class_name}.log")

    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.INFO)

    # Create a separate logger instance
    logger_name = f"{class_name}_logger"
    dedicated_logger = logging.getLogger(logger_name)
    dedicated_logger.setLevel(logging.INFO)
    dedicated_logger.handlers.clear()
    dedicated_logger.addHandler(handler)

    # Configure structlog to use this logger
    return structlog.wrap_logger(
        dedicated_logger,
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
    )
