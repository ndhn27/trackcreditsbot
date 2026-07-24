"""
Odesli (Song.link) API client for streaming platform links.

Converts any music URL to links on all major platforms.
"""

from __future__ import annotations

from typing import Dict, Optional
from urllib.parse import urlencode

from config import logger
from api.clients.base import ApiSessionManager

__all__ = ["OdesliClient"]


class OdesliClient:
    """Client for Odesli/Song.link API."""

    def __init__(self, session_manager: ApiSessionManager):
        self._session_manager = session_manager

    async def fetch_links(self, url: str) -> Optional[Dict]:
        """
        Fetch streaming links for a track across all platforms.

        Returns dict with:
        - linksByPlatform: dict of platform → URL mappings
        - entityUniqueId: unique track identifier
        - entitiesByUniqueId: platform-specific metadata (thumbnail, etc.)
        """
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            params = {"url": url, "userCountry": "US"}
            status, payload = await self._session_manager.fetch_json(
                f"https://api.song.link/v1-alpha.1/links?{urlencode(params)}",
                headers=headers,
                timeout=8,
                retries=2,
            )
            if status != 200 or not payload:
                logger.warning("Odesli failed [%s]: HTTP %s", url[:120], status)
                return None
            return payload
        except Exception as exc:
            logger.warning("Odesli request failed for %s: %s", url[:120], exc)
            return None
