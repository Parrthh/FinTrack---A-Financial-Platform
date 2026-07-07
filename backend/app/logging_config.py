"""Structured JSON logging via structlog.

Consistent shape: timestamp, level, service, message/event, context kwargs.
Three logical streams distinguished by the `stream` field:
  app   — errors, request handling, perf
  audit — security-relevant user actions (also persisted to audit_log table)
  jobs  — scraper / price-fetch / classification runs (Phases 2+)
In production these go to stdout and are picked up by the host's log viewer
(Render/Fly free tier) — no paid log service.
"""

import logging
import sys

import structlog


def configure_logging(env: str = "dev") -> None:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
            if env == "dev"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(stream: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger().bind(service="fintrack-api", stream=stream)


app_log = get_logger("app")
audit_log = get_logger("audit")
jobs_log = get_logger("jobs")
