"""Tests for the hardened tools module — cache TTL, search fallbacks."""

import time

import pytest

from app.tools import (
    _get_cached_search,
    _search_cache,
    _set_cached_search,
    SEARCH_CACHE_TTL_SECONDS,
    check_character_count,
    get_platform_best_practices,
)


# ── Search cache ──────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the search cache before each test."""
    _search_cache.clear()
    yield
    _search_cache.clear()


def test_cache_miss_returns_none():
    assert _get_cached_search("nonexistent query") is None


def test_cache_set_and_hit():
    _set_cached_search("test query", "some results")
    cached = _get_cached_search("test query")
    assert cached is not None
    assert cached["results"] == "some results"
    assert "timestamp" in cached


def test_cache_ttl_expiry():
    """Expired entries should be evicted and return None."""
    _search_cache["old query"] = {
        "results": "stale data",
        "timestamp": time.time() - SEARCH_CACHE_TTL_SECONDS - 10,
    }
    assert _get_cached_search("old query") is None
    # Should also be evicted from the cache dict
    assert "old query" not in _search_cache


def test_cache_fresh_entry_not_evicted():
    """Fresh entries within TTL should be returned."""
    _set_cached_search("fresh query", "fresh data")
    cached = _get_cached_search("fresh query")
    assert cached is not None
    assert cached["results"] == "fresh data"


# ── check_character_count tool ────────────────────────────────────


def test_character_count_under_limit():
    result = check_character_count.invoke({"text": "Hello", "platform": "twitter"})
    assert "OK" in result
    assert "5/280" in result


def test_character_count_over_limit():
    long_text = "x" * 300
    result = check_character_count.invoke({"text": long_text, "platform": "twitter"})
    assert "OVER LIMIT" in result
    assert "300/280" in result


def test_character_count_unknown_platform():
    result = check_character_count.invoke({"text": "hello", "platform": "tiktok"})
    assert "Unknown platform" in result


def test_character_count_linkedin():
    result = check_character_count.invoke({"text": "A post", "platform": "linkedin"})
    assert "OK" in result
    assert "/3000" in result


def test_character_count_instagram():
    result = check_character_count.invoke({"text": "Caption", "platform": "instagram"})
    assert "OK" in result
    assert "/2200" in result


# ── get_platform_best_practices tool ──────────────────────────────


def test_best_practices_twitter():
    result = get_platform_best_practices.invoke({"platform": "twitter"})
    assert "Twitter" in result
    assert "280" in result or "thread" in result.lower()


def test_best_practices_linkedin():
    result = get_platform_best_practices.invoke({"platform": "linkedin"})
    assert "LinkedIn" in result


def test_best_practices_instagram():
    result = get_platform_best_practices.invoke({"platform": "instagram"})
    assert "Instagram" in result


def test_best_practices_unknown_platform():
    result = get_platform_best_practices.invoke({"platform": "snapchat"})
    assert "Unknown platform" in result
