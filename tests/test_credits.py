"""
Tests for credits.py — atomic deduct_credits().

Covers the fix for the double-spend bug: the previous implementation used
SELECT ... FOR UPDATE followed by a separate UPDATE, but each ran through
its own db_execute() call (own connection, own auto-committed implicit
transaction), so the row lock never actually spanned both statements.
deduct_credits() must now check-and-decrement atomically in one round trip.

Note: credits.py does `from db import db_execute` at module import time
(unlike payment.py, which imports it lazily inside the function), so the
patch target here is `credits.db_execute`, not `db.db_execute`.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import credits


class TestDeductCredits:
    async def test_sufficient_balance_deducts_and_logs(self):
        """UPDATE ... RETURNING balance returns a row -> success, and the
        transaction gets logged (a second db_execute call, for the INSERT
        into credit_transactions)."""
        with patch("credits.db_execute", AsyncMock(return_value=19)) as mock_db:
            ok = await credits.deduct_credits(111, 1, "search")

        assert ok is True
        assert mock_db.await_count == 2
        update_query = mock_db.await_args_list[0].args[0]
        assert update_query.strip().startswith("UPDATE user_credits")
        assert "AND balance >= $2" in update_query
        assert "RETURNING balance" in update_query
        log_query = mock_db.await_args_list[1].args[0]
        assert "INSERT INTO credit_transactions" in log_query

    async def test_insufficient_balance_fails_without_logging(self):
        """WHERE balance >= $2 matches no row -> fetchval returns None ->
        deduct_credits returns False and never logs a transaction (only
        one db_execute call, not two)."""
        with patch("credits.db_execute", AsyncMock(return_value=None)) as mock_db:
            ok = await credits.deduct_credits(111, 100, "search")

        assert ok is False
        mock_db.assert_awaited_once()

    async def test_zero_balance_after_deduction_still_counts_as_success(self):
        """RETURNING balance can legitimately return 0 (spent down to
        exactly zero) — must be treated as success (`is None` check), not
        as falsy failure."""
        with patch("credits.db_execute", AsyncMock(return_value=0)):
            ok = await credits.deduct_credits(111, 20, "search")
        assert ok is True

    async def test_two_near_simultaneous_deductions_only_one_succeeds(self):
        """Simulates the race the old FOR-UPDATE-then-UPDATE implementation
        was vulnerable to: two calls to deduct_credits for the same user in
        quick succession. With an atomic conditional UPDATE, only the call
        whose WHERE clause still matches (simulated here as the first
        UPDATE returning a balance, the second returning None because the
        balance was already consumed) succeeds — the account can't be
        overdrawn."""
        outcomes = iter([19, 1, None])  # update->ok, log-insert, second update->blocked

        async def fake_db_execute(*args, **kwargs):
            return next(outcomes)

        with patch("credits.db_execute", fake_db_execute):
            first = await credits.deduct_credits(111, 1, "search")
            second = await credits.deduct_credits(111, 1, "search")

        assert first is True
        assert second is False
