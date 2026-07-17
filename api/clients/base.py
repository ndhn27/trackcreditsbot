"""
Base API infrastructure: HTTP session management and Circuit Breaker.

This module provides the core HTTP functionality and circuit breaker pattern
to protect against external API failures.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import aiohttp

from config import logger

__all__ = ["AsyncCircuitBreaker", "CircuitPermit", "ApiSessionManager"]

_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class CircuitPermit:
    """Permission token from circuit breaker."""

    __slots__ = ("allowed", "probe")

    def __init__(self, allowed: bool, probe: bool):
        self.allowed = allowed
        self.probe = probe


class AsyncCircuitBreaker:
    """
    Circuit breaker pattern for external APIs.
    
    Prevents cascading failures by cutting off requests when an API is failing.
    States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (recovery) → CLOSED
    """

    __slots__ = (
        "_name",
        "_failure_threshold",
        "_open_seconds",
        "_state",
        "_consecutive_failures",
        "_open_until",
        "_half_open_in_flight",
        "_lock",
    )

    def __init__(self, name: str, *, failure_threshold: int = 5, open_seconds: int = 60):
        self._name = name
        self._failure_threshold = max(1, int(failure_threshold))
        self._open_seconds = max(1, int(open_seconds))
        self._state = "CLOSED"
        self._consecutive_failures = 0
        self._open_until = 0.0
        self._half_open_in_flight = False
        self._lock = asyncio.Lock()

    async def acquire(self) -> CircuitPermit:
        """Request permission to make an API call."""
        now = time.monotonic()
        async with self._lock:
            if self._state == "OPEN":
                if now < self._open_until:
                    return CircuitPermit(False, False)
                # Try a probe request
                self._state = "HALF_OPEN"
                self._half_open_in_flight = True
                return CircuitPermit(True, True)

            if self._state == "HALF_OPEN":
                if self._half_open_in_flight:
                    return CircuitPermit(False, True)
                self._half_open_in_flight = True
                return CircuitPermit(True, True)

            return CircuitPermit(True, False)

    async def record_success(self) -> None:
        """Record successful API call."""
        async with self._lock:
            self._consecutive_failures = 0
            if self._state in ("OPEN", "HALF_OPEN"):
                self._state = "CLOSED"
            self._half_open_in_flight = False

    async def record_failure(self) -> None:
        """Record failed API call."""
        now = time.monotonic()
        async with self._lock:
            if self._state == "HALF_OPEN":
                self._state = "OPEN"
                self._open_until = now + self._open_seconds
                self._consecutive_failures = self._failure_threshold
                self._half_open_in_flight = False
                logger.warning("Circuit OPEN (half-open failure): %s", self._name)
                return

            if self._state == "OPEN":
                self._half_open_in_flight = False
                return

            self._consecutive_failures += 1
            if self._consecutive_failures >= self._failure_threshold:
                self._state = "OPEN"
                self._open_until = now + self._open_seconds
                self._half_open_in_flight = False
                logger.warning("Circuit OPEN: %s", self._name)


class ApiSessionManager:
    """
    Manages aiohttp ClientSession and circuit breakers for multiple APIs.
    
    Responsible for:
    - Creating and managing a single ClientSession
    - Managing circuit breakers per API host
    - Handling retries and timeouts
    """

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        self._session_lock = asyncio.Lock()

        self._circuits: dict[str, AsyncCircuitBreaker] = {
            "api.genius.com": AsyncCircuitBreaker("genius", failure_threshold=5, open_seconds=60),
            "musicbrainz.org": AsyncCircuitBreaker("musicbrainz", failure_threshold=5, open_seconds=60),
            "api.song.link": AsyncCircuitBreaker("odesli", failure_threshold=5, open_seconds=60),
        }

    async def start(self) -> None:
        """Initialize HTTP session."""
        await self.get_session()

    async def stop(self) -> None:
        """Close HTTP session."""
        await self.close_session()

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp ClientSession."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=20,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
                self._session = aiohttp.ClientSession(connector=connector)
            return self._session

    async def close_session(self) -> None:
        """Close HTTP session."""
        async with self._session_lock:
            session = self._session
            self._session = None
        if session and not session.closed:
            await session.close()

    def _get_circuit_for_url(self, url: str) -> Optional[AsyncCircuitBreaker]:
        """Get circuit breaker for given URL host."""
        try:
            host = (urlparse(url).hostname or "").lower()
        except Exception:
            return None
        return self._circuits.get(host)

    async def fetch_text(
        self,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 8,
        retries: int = 2,
    ) -> tuple[int, str]:
        """
        Fetch plain text response with circuit breaker protection.
        
        Returns: (status_code, text)
        """
        circuit = self._get_circuit_for_url(url)
        permit = None
        if circuit:
            permit = await circuit.acquire()
            if not permit.allowed:
                return 503, ""

        last_exc: Exception | None = None
        effective_retries = 0 if (permit and permit.probe) else retries
        for attempt in range(effective_retries + 1):
            try:
                session = await self.get_session()
                async with session.get(
                    url,
                    headers=headers or {},
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    if response.status in _RETRYABLE_STATUSES and attempt < effective_retries:
                        await response.read()
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    if response.status in _RETRYABLE_STATUSES and circuit:
                        await circuit.record_failure()
                    elif circuit:
                        await circuit.record_success()
                    return response.status, await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                if attempt < effective_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                logger.warning("HTTP text fetch failed [%s]: %s", url[:120], exc)
                if circuit:
                    await circuit.record_failure()
                raise
        if last_exc:
            raise last_exc
        return 599, ""

    async def fetch_json(
        self,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 8,
        retries: int = 2,
    ) -> tuple[int, Any]:
        """
        Fetch JSON response with circuit breaker protection.
        
        Returns: (status_code, parsed_json)
        """
        circuit = self._get_circuit_for_url(url)
        permit = None
        if circuit:
            permit = await circuit.acquire()
            if not permit.allowed:
                return 503, None

        last_exc: Exception | None = None
        effective_retries = 0 if (permit and permit.probe) else retries
        for attempt in range(effective_retries + 1):
            try:
                session = await self.get_session()
                async with session.get(
                    url,
                    headers=headers or {},
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    if response.status in _RETRYABLE_STATUSES and attempt < effective_retries:
                        await response.read()
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    try:
                        payload = await response.json(content_type=None)
                        if response.status in _RETRYABLE_STATUSES and circuit:
                            await circuit.record_failure()
                        elif circuit:
                            await circuit.record_success()
                        return response.status, payload
                    except ValueError:
                        text = await response.text()
                        logger.warning("Expected JSON but got non-JSON [%s]: %.120s", url[:120], text)
                        if circuit:
                            await circuit.record_failure()
                        return response.status, None
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                if attempt < effective_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                logger.warning("HTTP JSON fetch failed [%s]: %s", url[:120], exc)
                if circuit:
                    await circuit.record_failure()
                raise
        if last_exc:
            raise last_exc
        return 599, None
