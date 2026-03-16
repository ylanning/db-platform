"""Logging configuration for the application."""

import logging

import structlog


def configure_logging() -> None:
    """Configure standard logging and structlog with JSON output.

    Output example:
        {"timestamp": "2026-03-15T14:30:22Z", "level": "info", "event": "Backup created"}
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
