"""Session store abstraction for grouping research runs by user session."""

from __future__ import annotations

from app.storage.database.models import SessionRecord


class SessionStore:
    """In-memory session registry used as a stable storage boundary."""

    def __init__(self, initial: dict[str, SessionRecord] | None = None) -> None:
        self._items: dict[str, SessionRecord] = dict(initial or {})

    def save(self, session: SessionRecord) -> SessionRecord:
        self._items[session.session_id] = session
        return session

    def get(self, session_id: str) -> SessionRecord:
        if session_id not in self._items:
            raise KeyError(session_id)
        return self._items[session_id]

    def list(self) -> list[SessionRecord]:
        return list(self._items.values())

    def delete(self, session_id: str) -> None:
        if session_id in self._items:
            del self._items[session_id]


__all__ = ["SessionStore"]
