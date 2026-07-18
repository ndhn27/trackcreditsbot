"""
MusicBrainz API client for recording metadata.

Handles:
- ISRC code lookup
- Label information
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional
from urllib.parse import urlencode

from config import logger
from metrics import metric_inc
from api.clients.base import ApiSessionManager

__all__ = ["MusicBrainzClient"]


class MusicBrainzClient:
    """Client for MusicBrainz API."""

    def __init__(self, session_manager: ApiSessionManager):
        self._session_manager = session_manager
        self._user_agent = "TrackCreditsBot/14.0 (https://github.com/trackcredits)"
        self._rate_lock = asyncio.Lock()
        self._next_request_at = 0.0

    async def fetch_metadata(self, title: str, artist: str) -> Optional[Dict]:
        """
        Fetch recording metadata from MusicBrainz.

        Returns dict with:
        - isrc: International Standard Recording Code
        - label: Record label
        - mb_id: MusicBrainz recording ID
        - score: Search score

        Returns None immediately if the rate-limit queue is too deep (> 2 s
        backlog).  MusicBrainz is supplementary metadata; it is never worth
        blocking the whole gather() call chain for many seconds.
        """
        if not title:
            return None

        try:
            query = f'recording:"{title}" AND artist:"{artist}"' if artist else f'recording:"{title}"'
            params = {"query": query, "fmt": "json", "limit": 1}
            headers = {"User-Agent": self._user_agent, "Accept": "application/json"}

            # Rate limit: MusicBrainz requires 1 second between requests.
            # Returns False when the queue backlog exceeds the cap — skip
            # the request rather than making every concurrent caller wait.
            if not await self._rate_limit():
                logger.debug(
                    "MusicBrainz queue full, skipping supplementary lookup for %s / %s",
                    title, artist,
                )
                return None

            status, payload = await self._session_manager.fetch_json(
                f"https://musicbrainz.org/ws/2/recording/?{urlencode(params)}",
                headers=headers,
                timeout=8,
                retries=1,
            )

            if status != 200 or not payload:
                metric_inc("mb_err")
                logger.warning("MusicBrainz failed for %s / %s: HTTP %s", title, artist, status)
                return None

            recordings = payload.get("recordings", [])
            if not recordings:
                return None

            recording = recordings[0]
            isrc_list = recording.get("isrcs", [])
            label = ""

            for release in recording.get("releases", [])[:1]:
                for label_info in release.get("label-info", [])[:1]:
                    label_data = label_info.get("label", {})
                    if label_data.get("name"):
                        label = label_data["name"]

            metric_inc("mb_ok")
            return {
                "isrc": isrc_list[0] if isrc_list else "",
                "label": label,
                "mb_id": recording.get("id", ""),
                "score": recording.get("score", 0),
            }
        except Exception as exc:
            metric_inc("mb_err")
            logger.warning("MusicBrainz request error for %s / %s: %s", title, artist, exc)
            return None

    # Maximum time a request is willing to wait in the rate-limit queue.
    # Beyond this the request is dropped (MusicBrainz is supplementary).
    _MAX_QUEUE_WAIT = 2.0

    async def _rate_limit(self) -> bool:
        """
        Enforce MusicBrainz's 1-request-per-second policy.

        Returns True if the caller should proceed with the HTTP request,
        False if the queue backlog exceeds ``_MAX_QUEUE_WAIT`` seconds and
        the request should be skipped.

        The old implementation accumulated ``_next_request_at += 1.0`` for
        every waiter inside the lock, so 20 concurrent requests would
        schedule slots at t+0 s, t+1 s, … t+19 s — the last caller waits
        19 seconds.  The fix: measure the expected wait *before* committing
        to a slot.  If the wait exceeds the cap, bail out without advancing
        the queue pointer.
        """
        async with self._rate_lock:
            now = time.monotonic()
            scheduled = max(now, self._next_request_at)
            wait = scheduled - now
            if wait > self._MAX_QUEUE_WAIT:
                # Queue is too deep — drop this supplementary request.
                return False
            # Commit the slot only after confirming we will use it.
            self._next_request_at = scheduled + 1.0

        if wait > 0:
            await asyncio.sleep(wait)
        return True
