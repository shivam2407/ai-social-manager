"""Tests for the circuit breaker pattern."""

import asyncio
import time

import pytest

from app.circuit_breaker import CircuitBreaker, CircuitOpenError


@pytest.fixture
def breaker():
    """A circuit breaker that opens after 2 failures, resets after 0.2s."""
    return CircuitBreaker(failure_threshold=2, reset_timeout=0.2, name="test")


def _make_flaky_fn(breaker, fail_count):
    """Create an async function that fails `fail_count` times then succeeds."""
    calls = {"n": 0}

    @breaker
    async def fn():
        calls["n"] += 1
        if calls["n"] <= fail_count:
            raise RuntimeError("boom")
        return "ok"

    return fn, calls


# ── Closed state (normal) ────────────────────────────────────────


def test_passes_through_when_closed(breaker):
    @breaker
    async def fn():
        return "hello"

    result = asyncio.get_event_loop().run_until_complete(fn())
    assert result == "hello"
    assert breaker.failure_count == 0
    assert breaker.is_open is False


def test_increments_failure_count(breaker):
    @breaker
    async def fn():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        asyncio.get_event_loop().run_until_complete(fn())

    assert breaker.failure_count == 1
    assert breaker.is_open is False  # threshold is 2, only 1 failure


# ── Open state (tripped) ─────────────────────────────────────────


def test_opens_after_threshold(breaker):
    @breaker
    async def fn():
        raise RuntimeError("fail")

    loop = asyncio.get_event_loop()

    # First failure
    with pytest.raises(RuntimeError):
        loop.run_until_complete(fn())
    assert breaker.is_open is False

    # Second failure — hits threshold
    with pytest.raises(RuntimeError):
        loop.run_until_complete(fn())
    assert breaker.is_open is True
    assert breaker.failure_count == 2


def test_rejects_when_open(breaker):
    # Force the breaker open
    breaker.is_open = True
    breaker.last_failure_time = time.time()

    @breaker
    async def fn():
        return "should not reach"

    with pytest.raises(CircuitOpenError) as exc_info:
        asyncio.get_event_loop().run_until_complete(fn())

    assert "test" in str(exc_info.value)


# ── Half-open state (probing) ────────────────────────────────────


def test_half_open_after_timeout(breaker):
    """After reset_timeout, one request is allowed through (half-open)."""
    breaker.is_open = True
    breaker.last_failure_time = time.time() - 1.0  # well past 0.2s timeout

    @breaker
    async def fn():
        return "recovered"

    result = asyncio.get_event_loop().run_until_complete(fn())
    assert result == "recovered"
    assert breaker.is_open is False
    assert breaker.failure_count == 0


def test_half_open_failure_reopens(breaker):
    """If the half-open probe fails, the circuit re-opens."""
    breaker.is_open = True
    breaker.failure_count = 2
    breaker.last_failure_time = time.time() - 1.0  # past timeout

    @breaker
    async def fn():
        raise RuntimeError("still broken")

    loop = asyncio.get_event_loop()
    with pytest.raises(RuntimeError):
        loop.run_until_complete(fn())

    # Half-open sets is_open=False but doesn't reset failure_count.
    # The probe failure increments it to 3, which >= threshold (2),
    # so the circuit re-opens immediately.
    assert breaker.failure_count == 3
    assert breaker.is_open is True


# ── Success resets counter ────────────────────────────────────────


def test_success_resets_failure_count(breaker):
    fn, calls = _make_flaky_fn(breaker, fail_count=1)
    loop = asyncio.get_event_loop()

    # First call fails
    with pytest.raises(RuntimeError):
        loop.run_until_complete(fn())
    assert breaker.failure_count == 1

    # Second call succeeds — counter should reset
    result = loop.run_until_complete(fn())
    assert result == "ok"
    assert breaker.failure_count == 0


# ── CircuitOpenError ──────────────────────────────────────────────


def test_circuit_open_error_has_name():
    err = CircuitOpenError("my_service")
    assert err.name == "my_service"
    assert "my_service" in str(err)
