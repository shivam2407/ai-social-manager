"""Shared LLM response parsing — works across all providers."""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_text(content) -> str:
    """Normalize LLM response content to a plain string.

    Handles differences between providers:
    - Most return a plain string
    - Claude can return a list of content blocks: [{"type": "text", "text": "..."}]
    - Some return a list of dicts with just a "text" key
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
        return " ".join(parts)
    return str(content)


def _sanitize_json(text: str) -> str:
    """Fix common LLM JSON issues: control chars inside strings."""
    return re.sub(
        r'(?<=": ")(.*?)(?=")',
        lambda m: m.group(0).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"),
        text,
        flags=re.DOTALL,
    )


def extract_json(text: str) -> str | None:
    """Extract a JSON object from text that may contain markdown fences.

    Handles:
    - ```json ... ``` blocks (case-insensitive)
    - Plain ``` ... ``` blocks
    - Bare JSON (first { to last })
    - Missing closing fences
    """
    # Try ```json block (case-insensitive)
    match = re.search(r"```[jJ][sS][oO][nN]\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return _sanitize_json(match.group(1).strip())

    # Try plain ``` block
    match = re.search(r"```\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        if candidate.startswith("{"):
            return _sanitize_json(candidate)

    # Fallback: first { to last }
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        return _sanitize_json(text[brace_start : brace_end + 1])

    return None


def parse_json_response(content, fallback: dict | None = None) -> dict:
    """Full pipeline: normalize content -> extract JSON -> parse.

    Returns parsed dict or fallback on any failure.
    """
    if fallback is None:
        fallback = {}
    try:
        text = extract_text(content)
        json_str = extract_json(text)
        if json_str:
            return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning("JSON parse failed: %s", e)
    return fallback
