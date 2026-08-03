"""
app/llm/parser.py
=================
Structured output parser that extracts and validates JSON from LLM responses
against Pydantic models. Handles common LLM output quirks and formatting issues.
"""

import json
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.harness.exceptions import LLMOutputParseError
from app.observability.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# Matches ```json ... ``` and ``` ... ``` fenced code blocks
_JSON_FENCE_PATTERN = re.compile(
    r"```(?:json)?\s*([\s\S]*?)```",
    re.IGNORECASE | re.DOTALL,
)


def _extract_json_string(raw: str) -> str:
    """
    Extracts the raw JSON string from an LLM response.
    Strips markdown code fences if present. Falls back to the entire string.

    Args:
        raw: Raw text output from the LLM.

    Returns:
        Extracted JSON string candidate.
    """
    # Try to find a ```json ... ``` or ``` ... ``` block first
    match = _JSON_FENCE_PATTERN.search(raw)
    if match:
        return match.group(1).strip()

    # Try to find a bare JSON object {...} or array [...]
    raw = raw.strip()
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = raw.find(start_char)
        end = raw.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            return raw[start:end + 1]

    return raw


def _sanitize_json(raw_json: str) -> str:
    """
    Applies light sanitization to handle common LLM JSON output quirks:
    - Trailing commas before closing brackets (e.g., [1, 2, 3,])
    - Smart quotes ("") replaced with standard quotes ("")
    """
    # Remove trailing commas before } or ]
    sanitized = re.sub(r",\s*([}\]])", r"\1", raw_json)

    # Normalize smart/curly quotes to standard ASCII quotes
    sanitized = sanitized.replace("\u201c", '"').replace("\u201d", '"')
    sanitized = sanitized.replace("\u2018", "'").replace("\u2019", "'")

    return sanitized


def parse_llm_output(
    raw: str,
    response_model: Type[T],
    node: str = "unknown",
    model_name: str = "unknown",
) -> T:
    """
    Parses and validates a raw LLM string response against a Pydantic model.

    Steps:
        1. Extract JSON string (strip markdown fences).
        2. Sanitize common formatting issues.
        3. Parse JSON with standard library.
        4. Validate parsed dict against the target Pydantic model.

    Args:
        raw: Raw text output from the LLM.
        response_model: The Pydantic class to validate against.
        node: The calling graph node name (for error context).
        model_name: The LLM model that produced the output (for error context).

    Returns:
        A validated instance of the specified Pydantic model.

    Raises:
        LLMOutputParseError: If extraction, JSON parsing, or Pydantic validation fails.
    """
    # Step 1: Extract the JSON string candidate
    json_candidate = _extract_json_string(raw)

    # Step 2: Sanitize
    json_candidate = _sanitize_json(json_candidate)

    # Step 3: Parse JSON
    try:
        data: Any = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        logger.warning(
            "LLM JSON parse failed.",
            node=node,
            model=model_name,
            raw_preview=raw[:300],
            error=str(exc),
        )
        raise LLMOutputParseError(
            message=f"LLM output could not be parsed as JSON: {exc}",
            model_name=model_name,
        ) from exc

    # Step 4: Validate against Pydantic schema
    try:
        return response_model.model_validate(data)
    except ValidationError as exc:
        logger.warning(
            "LLM Pydantic validation failed.",
            node=node,
            model=model_name,
            target_schema=response_model.__name__,
            error=str(exc),
        )
        raise LLMOutputParseError(
            message=f"LLM output failed schema validation for '{response_model.__name__}': {exc}",
            model_name=model_name,
        ) from exc
