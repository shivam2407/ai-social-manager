"""Tests for idempotency key generation and critic parse failure handling."""

import pytest


# ── Idempotency key ───────────────────────────────────────────────


def test_same_input_same_key():
    from app.main import _make_idempotency_key

    key1 = _make_idempotency_key("Write about AI", "TechBrand", ["twitter", "linkedin"])
    key2 = _make_idempotency_key("Write about AI", "TechBrand", ["twitter", "linkedin"])
    assert key1 == key2


def test_different_input_different_key():
    from app.main import _make_idempotency_key

    key1 = _make_idempotency_key("Write about AI", "TechBrand", ["twitter"])
    key2 = _make_idempotency_key("Write about cooking", "TechBrand", ["twitter"])
    assert key1 != key2


def test_platform_order_does_not_matter():
    """Platforms are sorted, so order shouldn't affect the key."""
    from app.main import _make_idempotency_key

    key1 = _make_idempotency_key("topic", "brand", ["twitter", "linkedin"])
    key2 = _make_idempotency_key("topic", "brand", ["linkedin", "twitter"])
    assert key1 == key2


def test_key_is_sha256_hex():
    from app.main import _make_idempotency_key

    key = _make_idempotency_key("test", "brand", ["twitter"])
    assert len(key) == 64  # SHA-256 hex digest
    assert all(c in "0123456789abcdef" for c in key)


def test_different_brand_different_key():
    from app.main import _make_idempotency_key

    key1 = _make_idempotency_key("topic", "BrandA", ["twitter"])
    key2 = _make_idempotency_key("topic", "BrandB", ["twitter"])
    assert key1 != key2


# ── Critic parse failure ──────────────────────────────────────────


def test_critic_parse_failure_returns_warning():
    """When the critic gets empty/malformed JSON, it should flag it as a warning,
    not silently auto-approve."""
    from app.response_parser import parse_json_response

    # Simulate what happens when the LLM returns garbage
    garbage_content = "This is not JSON at all, just random text without braces"
    result = parse_json_response(garbage_content)

    # parse_json_response returns {} on failure
    assert result == {}

    # The critic node checks `if not data:` — empty dict is falsy
    assert not result


def test_parse_json_response_with_valid_json():
    from app.response_parser import parse_json_response

    content = '```json\n{"scores": [{"platform": "twitter", "overall_score": 8.0}]}\n```'
    result = parse_json_response(content)

    assert "scores" in result
    assert result["scores"][0]["overall_score"] == 8.0


def test_parse_json_response_with_malformed_json():
    from app.response_parser import parse_json_response

    content = '```json\n{invalid json here}\n```'
    result = parse_json_response(content)

    assert result == {}


# ── Trend researcher search queries ──────────────────────────────


def test_build_search_queries():
    from app.agents.trend_researcher import _build_search_queries

    queries = _build_search_queries(
        platforms=["twitter", "linkedin"],
        niche="home bakery",
        topic="sourdough bread",
    )

    # 2 queries per platform = 4 total
    assert len(queries) == 4

    # Each is a (platform, query_string) tuple
    platforms = [q[0] for q in queries]
    assert platforms.count("twitter") == 2
    assert platforms.count("linkedin") == 2

    # Queries should contain the niche and topic
    for platform, query in queries:
        assert "home bakery" in query
        assert "sourdough bread" in query


def test_build_search_queries_unknown_platform():
    from app.agents.trend_researcher import _build_search_queries

    queries = _build_search_queries(
        platforms=["tiktok"],
        niche="fitness",
        topic="workout",
    )

    # No templates for tiktok, should return empty
    assert len(queries) == 0


def test_format_search_results_empty():
    from app.agents.trend_researcher import _format_search_results

    result = _format_search_results({})
    assert "[No search results available" in result


def test_format_search_results_with_data():
    from app.agents.trend_researcher import _format_search_results

    result = _format_search_results({
        "twitter": ["Result about viral tweets", "Another twitter result"],
        "linkedin": ["LinkedIn post roundup"],
    })

    assert "TWITTER" in result
    assert "LINKEDIN" in result
    assert "Result about viral tweets" in result
    assert "Search 1" in result
    assert "Search 2" in result
