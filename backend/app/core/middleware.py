"""Request context, security headers and JSON access logging (architecture section 5, SEC-15, SEC-21).

Pure ASGI (not BaseHTTPMiddleware) so that background tasks and streaming responses are unaffected, and so that an
unexpected exception is turned into a 500 problem+json that still carries the request id and security headers.

Logged per request: method, route template, status, latency_ms, user_id, request_id. Never logged: bodies, headers,
query strings, tokens, passwords, note or issue text.
"""
import json
import logging
import re
import sys
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import problem_response

access_log = logging.getLogger("gurusetu.access")
error_log = logging.getLogger("gurusetu.error")

_REQUEST_ID_OK = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}


class JsonFormatter(logging.Formatter):
    """One JSON object per line. A dict message is merged into the line."""

    def format(self, record: logging.LogRecord) -> str:
        line: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
        }
        if isinstance(record.msg, dict):
            line.update(record.msg)
        else:
            line["msg"] = record.getMessage()
        if record.exc_info:
            line["exc"] = self.formatException(record.exc_info)
        return json.dumps(line, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # uvicorn's own access log would duplicate ours (and prints the full path with query string).
    logging.getLogger("uvicorn.access").disabled = True


def _level_for(status: int, route_matched: bool) -> int:
    if status >= 500:
        return logging.ERROR
    if status in (401, 403, 429) or (status == 404 and route_matched):
        return logging.WARNING  # security-relevant (SEC-13)
    return logging.INFO


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        supplied = Headers(scope=scope).get("x-request-id")
        request_id = supplied if supplied and _REQUEST_ID_OK.match(supplied) else uuid.uuid4().hex
        state = scope.setdefault("state", {})
        state["request_id"] = request_id

        status = 500
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            error_log.exception({"event": "unhandled_exception", "request_id": request_id})
            if response_started:
                raise
            response = problem_response(
                "INTERNAL", 500, "Something went wrong on our side.", scope.get("path"), request_id
            )
            await response(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            access_log.log(
                _level_for(status, route is not None),
                {
                    "event": "request",
                    "method": scope.get("method"),
                    "route": getattr(route, "path", "unmatched"),
                    "status": status,
                    "latency_ms": round((time.perf_counter() - started_at) * 1000, 1),
                    "user_id": state.get("user_id"),
                    "request_id": request_id,
                },
            )
