"""Error model (backend.md section 3.1): every error is RFC 9457 application/problem+json with a stable `code`.

Services raise `ApiError(code, status, detail)`. Validation errors become 422 VALIDATION_FAILED; HTTPException keeps
its status (it is never swallowed into a 500); anything else is handled in `core/middleware.py` as 500 INTERNAL.
Never put request bodies, tokens or note/issue text in `detail` (SEC-15).
"""
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from neo4j.exceptions import ServiceUnavailable
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_MEDIA_TYPE = "application/problem+json"
ERROR_BASE_URL = "https://gurusetu.local/errors/"

# code -> (title, default HTTP status). Additive to the table in backend.md section 3.1.
CODES: dict[str, tuple[str, int]] = {
    "UNAUTHENTICATED": ("Authentication required", 401),
    "TOKEN_EXPIRED": ("Session expired", 401),
    "INVALID_CREDENTIALS": ("Invalid credentials", 401),
    "FORBIDDEN": ("Forbidden", 403),
    "NOT_FOUND": ("Not found", 404),
    "METHOD_NOT_ALLOWED": ("Method not allowed", 405),
    "VALIDATION_FAILED": ("Validation failed", 422),
    "NOT_YOUR_MENTEE": ("Not your mentee", 422),
    "ALREADY_APPLIED": ("Already applied", 409),
    "INVALID_TRANSITION": ("Invalid status transition", 409),
    "NOT_PRESENT": ("Not marked present", 409),
    "OPENING_CLOSED": ("Opening is closed", 409),
    "ALREADY_REVIEWED": ("Already reviewed", 409),
    "FILE_TOO_LARGE": ("File too large", 413),
    "UNSUPPORTED_FILE_TYPE": ("Unsupported file type", 415),
    "RATE_LIMITED": ("Too many requests", 429),
    "DB_UNAVAILABLE": ("Service unavailable", 503),
    "INTERNAL": ("Internal error", 500),
}

_STATUS_TO_CODE = {
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "FILE_TOO_LARGE",
    415: "UNSUPPORTED_FILE_TYPE",
    422: "VALIDATION_FAILED",
    429: "RATE_LIMITED",
    503: "DB_UNAVAILABLE",
}

_LOC_PREFIXES = {"body", "query", "path", "header", "cookie"}


class ApiError(Exception):
    """A handled, user-visible error."""

    def __init__(
        self,
        code: str,
        status: int | None = None,
        detail: str = "",
        errors: Sequence[Mapping[str, str]] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status if status is not None else CODES.get(code, ("", 500))[1]
        self.detail = detail
        self.errors = list(errors) if errors else None
        self.headers = dict(headers) if headers else None


def _kebab(code: str) -> str:
    return code.lower().replace("_", "-")


def problem_body(
    code: str,
    status: int,
    detail: str = "",
    instance: str | None = None,
    request_id: str | None = None,
    errors: Sequence[Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    title = CODES.get(code, (code.replace("_", " ").capitalize(), status))[0]
    body: dict[str, Any] = {
        "type": ERROR_BASE_URL + _kebab(code),
        "title": title,
        "status": status,
        "code": code,
    }
    if detail:
        body["detail"] = detail
    if instance:
        body["instance"] = instance
    if request_id:
        body["request_id"] = request_id
    if errors is not None:
        body["errors"] = list(errors)
    return body


def problem_response(
    code: str,
    status: int,
    detail: str = "",
    instance: str | None = None,
    request_id: str | None = None,
    errors: Sequence[Mapping[str, str]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        problem_body(code, status, detail, instance, request_id, errors),
        status_code=status,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=dict(headers) if headers else None,
    )


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return problem_response(
        exc.code, exc.status, exc.detail, request.url.path, _request_id(request), exc.errors, exc.headers
    )


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Only the field path and Pydantic's message are returned: never the submitted value (it may be a password).
    errors = [
        {
            "field": ".".join(str(part) for part in err.get("loc", ()) if part not in _LOC_PREFIXES) or "request",
            "message": str(err.get("msg", "Invalid value")),
        }
        for err in exc.errors()
    ]
    return problem_response(
        "VALIDATION_FAILED", 422, "Request validation failed.", request.url.path, _request_id(request), errors
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_TO_CODE.get(exc.status_code, "INTERNAL" if exc.status_code >= 500 else f"HTTP_{exc.status_code}")
    detail = exc.detail if isinstance(exc.detail, str) else ""
    if exc.status_code == 404:
        detail = "The resource was not found."
    return problem_response(
        code, exc.status_code, detail, request.url.path, _request_id(request), headers=exc.headers
    )


async def _db_unavailable_handler(request: Request, exc: ServiceUnavailable) -> JSONResponse:
    return problem_response(
        "DB_UNAVAILABLE",
        503,
        "The database is not reachable. Try again in a moment.",
        request.url.path,
        _request_id(request),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(ServiceUnavailable, _db_unavailable_handler)
