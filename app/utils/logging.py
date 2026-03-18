"""Logging configuration for the application."""

from __future__ import annotations

import contextvars
import logging
import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog

CONTEXT_REQUEST_INFO: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "request_info", default={}
)


def _add_request_context(
    logger: object, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Attach request-scoped context fields to structured log events.

    Example:
        with log_request_info(request_id="abc123", path="/health"):
            logger.info("request_started")

        # Emitted JSON:
        # {
            "timestamp":"...",
            "level":"info",
            "event":"request_started",
            "request_id":"abc123",
            "path":"/health"
            }
    """
    ctx = CONTEXT_REQUEST_INFO.get() or {}
    event_dict.update(ctx)
    return event_dict


def configure_logging() -> None:
    """Configure standard logging and structlog with JSON output.

    Output example:
        {"timestamp": "2026-03-15T14:30:22Z", "level": "info", "event": "Backup created"}
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = logging.getLevelName(level_name)
    if isinstance(level, str):
        level = logging.INFO
    processors = [
        _add_request_context,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[*processors, structlog.processors.JSONRenderer()],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


@contextmanager
def log_request_info(**fields: object) -> Generator[None, None, None]:
    """Bind request-scoped fields to structured logs for the current context.

    Example:
        with log_request_info(request_id="abc123", method="GET", path="/health"):
            logger.info("request_started")
    """
    current_ctx = CONTEXT_REQUEST_INFO.get() or {}
    merged_ctx = {**current_ctx, **fields}
    token = CONTEXT_REQUEST_INFO.set(merged_ctx)
    try:
        yield
    finally:
        CONTEXT_REQUEST_INFO.reset(token)
