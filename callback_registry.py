"""
Callback registry for routing Telegram callback_data strings to async handlers.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

__all__ = ["CallbackRegistry"]

CallbackHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE, str], Awaitable[None]]


class CallbackRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, CallbackHandler] = {}

    def register(self, prefix: str):
        """
        Register an async callback handler.

        Matching rules:
        - Exact match: data == prefix -> payload = ""
        - Prefix match: data.startswith(prefix + "_") -> payload is remainder after "prefix_"
        """

        if not isinstance(prefix, str) or not prefix:
            raise ValueError("prefix must be a non-empty string")

        def _decorator(fn: CallbackHandler) -> CallbackHandler:
            if prefix in self._handlers:
                raise ValueError(f"Callback prefix already registered: {prefix!r}")
            self._handlers[prefix] = fn
            return fn

        return _decorator

    async def dispatch(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not query.data:
            return

        # Always ack callbacks first so Telegram UI doesn't show "loading..." if we error.
        try:
            await query.answer()
        except Exception:
            pass

        data = query.data

        handler = self._handlers.get(data)
        if handler is not None:
            await handler(update, context, "")
            return

        best_prefix: Optional[str] = None
        for prefix in self._handlers.keys():
            if data.startswith(prefix + "_"):
                if best_prefix is None or len(prefix) > len(best_prefix):
                    best_prefix = prefix

        if best_prefix is None:
            raise ValueError(f"No callback route for {data!r}")

        payload = data[len(best_prefix) + 1 :]
        await self._handlers[best_prefix](update, context, payload)

