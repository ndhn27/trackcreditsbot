"""
Application context (DI container) for TrackCredits.

This module defines Protocols for mocking and a small AppContext dataclass for lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from api import ApiClient
from db import Database


class DatabaseProto(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def init_db(self) -> None: ...

    async def execute(
        self,
        query: str,
        params: Sequence[Any] = (),
        *,
        fetch: bool = False,
        fetch_all: bool = False,
        returning: bool = False,
    ) -> Any: ...

    async def add_score(self, user_id: int, username: str, points: int) -> None: ...

    async def store_track_hash(self, track_key: str, track_hash: str | None = None) -> str: ...

    async def get_track_key_from_hash(self, track_hash: str) -> str | None: ...


class ApiClientProto(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def async_get_text(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 8,
    ) -> str: ...

    async def async_get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 8,
    ) -> Any: ...

    async def fetch_musicbrainz_data(self, title: str, artist: str) -> dict | None: ...

    async def fetch_genius_search(self, query: str, limit: int = 10) -> list[dict]: ...

    async def fetch_genius_data(self, title: str, artist: str) -> dict | None: ...

    async def fetch_auto_lyrics(self, title: str, artist: str) -> str | None: ...

    async def get_odesli(self, url: str) -> dict | None: ...


@dataclass(slots=True)
class AppContext:
    db: DatabaseProto
    api: ApiClientProto

    async def start(self) -> None:
        await self.db.start()
        await self.db.init_db()
        await self.api.start()

    async def stop(self) -> None:
        await self.api.stop()
        await self.db.stop()


def make_default_db() -> Database:
    return Database()


def make_default_api() -> ApiClient:
    return ApiClient()


# Module-level bot reference — set by main.py post_init via set_bot().
# Used by health.py and dashboard.py to send Telegram notifications
# without importing the full PTB Application object.
_BOT_INSTANCE: Any = None


def set_bot(bot: Any) -> None:
    """Store the PTB Bot instance for use by webhook/dashboard handlers."""
    global _BOT_INSTANCE
    _BOT_INSTANCE = bot

