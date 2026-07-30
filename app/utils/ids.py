"""
app/utils/ids.py
================
Centralized ID generation for the research agent.

Every entity in the system gets a typed, prefixed ID so that
at a glance you can tell what kind of object you're looking at.

Examples:
    run_7f94a3b2c1d04e5f
    task_1a2b3c4d5e6f7a8b
    src_9z8y7x6w5v4u3t2s

All IDs are:
- Globally unique (UUID4 under the hood)
- URL-safe (no special characters)
- Sortable within the same second (timestamp prefix optional)
- Human-readable prefix for debugging
"""

from __future__ import annotations

import uuid


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------


def _make_id(prefix: str) -> str:
    """Generate a prefixed UUID4-based ID with no hyphens."""
    uid = uuid.uuid4().hex  # 32 hex chars, no hyphens
    return f"{prefix}_{uid}"


# ---------------------------------------------------------------------------
# Typed ID generators — one per entity
# ---------------------------------------------------------------------------


def new_run_id() -> str:
    """
    Unique ID for a single execution attempt of the research agent.
    Example: run_7f94a3b2c1d04e5f8a9b0c1d2e3f4a5b
    """
    return _make_id("run")


def new_thread_id() -> str:
    """
    Persistent conversation/workflow identity across multiple runs.
    Example: thread_1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d
    """
    return _make_id("thread")


def new_session_id() -> str:
    """
    Optional higher-level application session grouping multiple threads.
    Example: session_9z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4
    """
    return _make_id("session")


def new_task_id() -> str:
    """
    ID for a single ResearchTask within a plan.
    Example: task_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
    """
    return _make_id("task")


def new_plan_id() -> str:
    """
    ID for a ResearchPlan produced by the Planner node.
    Example: plan_f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6
    """
    return _make_id("plan")


def new_finding_id() -> str:
    """
    ID for a single Finding extracted by the Researcher.
    Example: find_0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d
    """
    return _make_id("find")


def new_source_id() -> str:
    """
    ID for a Source (web page, PDF, etc.) discovered during research.
    Example: src_5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a
    """
    return _make_id("src")


def new_gap_id() -> str:
    """
    ID for a ResearchGap identified by the Critic.
    Example: gap_2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b
    """
    return _make_id("gap")


def new_critique_id() -> str:
    """
    ID for a Critique pass produced by the Critic node.
    Example: crit_b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6
    """
    return _make_id("crit")


def new_report_id() -> str:
    """
    ID for a FinalReport produced by the Writer node.
    Example: rpt_e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
    """
    return _make_id("rpt")


def new_citation_id() -> str:
    """
    ID for a Citation within a report.
    Example: cite_3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f
    """
    return _make_id("cite")


def new_event_id() -> str:
    """
    ID for a harness lifecycle or progress event.
    Example: evt_9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d
    """
    return _make_id("evt")


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------


def is_valid_id(value: str, prefix: str) -> bool:
    """
    Check that a string looks like a valid prefixed ID.

    Args:
        value:  The string to validate (e.g. "run_7f94a3b2c1d04e5f...")
        prefix: Expected prefix without underscore (e.g. "run")

    Returns:
        True if the format matches prefix_<32 hex chars>.
    """
    expected_prefix = f"{prefix}_"
    if not value.startswith(expected_prefix):
        return False
    hex_part = value[len(expected_prefix):]
    if len(hex_part) != 32:
        return False
    return all(c in "0123456789abcdef" for c in hex_part)
