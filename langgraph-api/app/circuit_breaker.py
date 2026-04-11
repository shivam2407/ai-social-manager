"""Circuit breaker pattern for external tool calls.

Prevents cascading failures when a dependency (e.g., DuckDuckGo search API)
becomes degraded. After `failure_threshold` consecutive failures, the circuit
opens and fails fast for `reset_timeout` seconds instead of hanging on a
slow dependency and dragging the entire pipeline down.

See: https://martinfowler.com/bliki/CircuitBreaker.html
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open and the call is rejected."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Circuit breaker '{name}' is open — failing fast")


class CircuitBreaker:
    """Simple circuit breaker with three states: closed, open, half-open.

    - **Closed** (normal): requests pass through. Failures increment a counter.
    - **Open** (tripped): requests are rejected immediately with CircuitOpenError.
    - **Half-open** (probing): after `reset_timeout` seconds, one request is
      allowed through to test if the dependency has recovered.

    Args:
        failure_threshold: consecutive failures before opening the circuit.
        reset_timeout: seconds to wait before entering half-open state.
        name: human-readable name for logging.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        name: str = "unnamed",
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False

    def __call__(self, func: Callable) -> Callable:
        """Use as a decorator on async functions."""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.is_open:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    logger.info(
                        "Circuit '%s' entering half-open state — allowing probe request",
                        self.name,
                    )
                    self.is_open = False  # half-open: allow one request
                else:
                    raise CircuitOpenError(self.name)

            try:
                result = await func(*args, **kwargs)
                # Success: reset failure count
                self.failure_count = 0
                return result
            except Exception:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.is_open = True
                    logger.warning(
                        "Circuit '%s' OPENED after %d consecutive failures",
                        self.name,
                        self.failure_count,
                    )
                raise

        return wrapper
