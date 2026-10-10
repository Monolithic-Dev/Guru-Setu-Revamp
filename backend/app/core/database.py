"""Neo4j access (CMP-12). One driver per process; all Cypher lives in `app/repos/` and calls these helpers.

Repository functions have the signature `fn(tx, **params)`. Services call `run_read(fn, **params)` or
`run_write(fn, **params)`; a write function receives the transaction so that notifications and StatusEvents are
written in the same transaction as the change (AGENTS.md hard rule).
"""
import logging
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from app.core.config import get_settings
from app.core.errors import ApiError

log = logging.getLogger("gurusetu.db")

_driver: Driver | None = None

_DB_DOWN = (ServiceUnavailable, SessionExpired)


def init_driver() -> Driver:
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    return _driver


def get_driver() -> Driver:
    return _driver if _driver is not None else init_driver()


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def wait_for_db(timeout_s: float = 60.0) -> None:
    """Block until Neo4j answers, retrying while it starts. Raises ServiceUnavailable on timeout."""
    deadline = time.monotonic() + timeout_s
    delay = 0.5
    while True:
        try:
            get_driver().verify_connectivity()
            return
        except _DB_DOWN as exc:
            if time.monotonic() >= deadline:
                raise
            log.warning("Neo4j not ready (%s); retrying", type(exc).__name__)
            time.sleep(delay)
            delay = min(delay * 1.5, 5.0)


def ping() -> bool:
    try:
        get_driver().verify_connectivity()
        return True
    except _DB_DOWN:
        return False


def run_read(fn: Callable[..., Any], **params: Any) -> Any:
    try:
        with get_driver().session() as session:
            return session.execute_read(fn, **params)
    except _DB_DOWN as exc:
        raise ApiError("DB_UNAVAILABLE", 503, "The database is not reachable. Try again in a moment.") from exc


def run_write(fn: Callable[..., Any], **params: Any) -> Any:
    try:
        with get_driver().session() as session:
            return session.execute_write(fn, **params)
    except _DB_DOWN as exc:
        raise ApiError("DB_UNAVAILABLE", 503, "The database is not reachable. Try again in a moment.") from exc


def schema_statements(text: str) -> list[str]:
    """Split schema.cypher into statements: drop `//` comment lines, split on semicolons."""
    without_comments = re.sub(r"(?m)^\s*//.*$", "", text)
    return [stmt.strip() for stmt in without_comments.split(";") if stmt.strip()]


def apply_schema(path: Path) -> int:
    """Apply constraints and indexes idempotently (every statement is `IF NOT EXISTS`). Returns the statement count."""
    statements = schema_statements(path.read_text(encoding="utf-8"))
    with get_driver().session() as session:
        for stmt in statements:
            session.run(stmt).consume()
    return len(statements)
