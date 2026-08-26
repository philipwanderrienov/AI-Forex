"""Structured logging helpers for the MT5 bridge.

Logs are intentionally small and event-oriented. Raw request bodies, credentials,
authorization headers, tokens, passwords, and connection strings must never be logged.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}

_SENSITIVE_FRAGMENTS = (
    "authorization",
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "connectionstring",
    "connection_string",
    "credential",
)


class JsonEventFormatter(logging.Formatter):
    """Render one JSON object per log line with automatic sensitive-field redaction."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = _redact(key, value)

        if record.exc_info:
            payload["exceptionType"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure process-wide JSON logging to stderr."""

    normalized = level.upper().strip()
    numeric_level = getattr(logging, normalized, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"invalid log level: {level}")

    handler = logging.StreamHandler()
    handler.setFormatter(JsonEventFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _redact(key: str, value: Any) -> Any:
    normalized = key.lower().replace("-", "_")
    if any(fragment in normalized for fragment in _SENSITIVE_FRAGMENTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(child_key): _redact(str(child_key), child_value) for child_key, child_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(key, item) for item in value]
    return value
