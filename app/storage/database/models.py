"""Database models for a storage-backed session and run registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SessionRecord:
    """Minimal session record stored for user or workflow grouping."""

    session_id: str
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


__all__ = ["SessionRecord"]
