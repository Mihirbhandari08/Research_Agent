"""Report retrieval service."""

from __future__ import annotations

from app.domain.report import FinalReport


class ReportService:
    """Read-only service for final generated reports."""

    def __init__(self, store: dict[str, FinalReport] | None = None) -> None:
        self.store = store or {}

    def get_report(self, report_id: str) -> FinalReport:
        if report_id not in self.store:
            raise KeyError(report_id)
        return self.store[report_id]
