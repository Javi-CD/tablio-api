"""Structured JSON logging and request-logging middleware."""

import json
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.config import settings
from app.core.security import decode_access_token


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    _SKIP = frozenset(
        {
            "args",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
            "taskName",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, val in record.__dict__.items():
            if key not in self._SKIP:
                data[key] = val
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def configure_logging() -> None:
    """Configure root logger with JSON output at the configured log level."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Our middleware handles request logging; suppress uvicorn's access log.
    logging.getLogger("uvicorn.access").propagate = False


logger = logging.getLogger("tablio")


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log every request: method, path, authenticated user, status, duration."""
    start = time.perf_counter()

    user_id: str | None = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            user_id = decode_access_token(auth[7:])
        except Exception:  # noqa: BLE001, S110 — invalid/expired tokens silently ignored
            user_id = None

    ctx: dict[str, object] = {
        "method": request.method,
        "path": request.url.path,
        "user_id": user_id,
    }

    try:
        response = await call_next(request)
    except Exception as exc:
        ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("request_error", extra={**ctx, "duration_ms": ms}, exc_info=exc)
        raise

    ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request",
        extra={**ctx, "status_code": response.status_code, "duration_ms": ms},
    )
    return response
