"""
Tests for payment.py — idempotent payment fulfillment.

Covers the fix for the double-credit bug: MoMo IPN and Stripe webhooks both
retry on non-2xx/slow responses, and Stripe will replay a validly-signed
event within its timestamp-tolerance window. fulfill_payment() must credit
a given order_id exactly once, no matter how many times it's called.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

import payment


class TestFulfillPaymentIdempotency:
    async def test_first_fulfillment_claims_order_and_adds_credits(self):
        """order_id not seen before -> INSERT ... RETURNING id succeeds (id=1)
        -> credits are added exactly once."""
        with patch("db.db_execute", AsyncMock(return_value=1)) as mock_db, \
             patch("credits.add_credits", AsyncMock(return_value=120)) as mock_add, \
             patch("credits.get_balance", AsyncMock()) as mock_bal:
            new_balance = await payment.fulfill_payment(111, "pack_120", "order_abc")

        assert new_balance == 120
        mock_add.assert_awaited_once_with(111, 120, "payment_order_abc")
        mock_bal.assert_not_awaited()
        query = mock_db.await_args.args[0]
        assert query.strip().startswith("INSERT INTO payment_orders")
        assert "ON CONFLICT (order_id) DO NOTHING" in query

    async def test_duplicate_order_id_does_not_double_credit(self):
        """Same order_id delivered again (webhook retry/replay): the
        ON CONFLICT DO NOTHING insert returns None (no row claimed) ->
        add_credits must NOT run again; existing balance is returned instead."""
        with patch("db.db_execute", AsyncMock(return_value=None)), \
             patch("credits.add_credits", AsyncMock(return_value=999)) as mock_add, \
             patch("credits.get_balance", AsyncMock(return_value=120)) as mock_bal:
            new_balance = await payment.fulfill_payment(111, "pack_120", "order_abc")

        assert new_balance == 120
        mock_add.assert_not_awaited()
        mock_bal.assert_awaited_once_with(111)

    async def test_unknown_package_raises_before_touching_db(self):
        with patch("db.db_execute", AsyncMock()) as mock_db:
            with pytest.raises(ValueError):
                await payment.fulfill_payment(111, "pack_nonexistent", "order_xyz")
        mock_db.assert_not_awaited()

    async def test_racing_duplicate_calls_only_credit_once(self):
        """Two 'simultaneous' deliveries of the same order: only the call
        that wins the UNIQUE constraint (simulated here as the first
        db_execute returning a row, the second returning None) results in
        add_credits being called."""
        outcomes = iter([1, None])

        async def fake_db_execute(*args, **kwargs):
            return next(outcomes)

        with patch("db.db_execute", fake_db_execute), \
             patch("credits.add_credits", AsyncMock(return_value=120)) as mock_add, \
             patch("credits.get_balance", AsyncMock(return_value=120)) as mock_bal:
            b1 = await payment.fulfill_payment(111, "pack_120", "order_race")
            b2 = await payment.fulfill_payment(111, "pack_120", "order_race")

        assert b1 == 120
        assert b2 == 120
        mock_add.assert_awaited_once()
        mock_bal.assert_awaited_once()
