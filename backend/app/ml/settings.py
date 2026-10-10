"""Access to P2's settings object from inside `ml/`.

`ml/` reads every threshold from configuration (backend.md §8); it never
hard-codes a value that has a setting. P2 exposes `get_settings()` rather than a
module-level singleton, and its field names are lower-case, so this is a thin
pass-through that keeps the import in one place and lets tests substitute a
fake without touching P2's module.
"""

from __future__ import annotations

from typing import Any


def get_settings() -> Any:
    """Return P2's cached settings instance (`app/core/config.py`)."""
    from app.core.config import get_settings as _get

    return _get()
