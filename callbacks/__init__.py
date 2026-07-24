"""
Exports all callback handlers.
"""
from callbacks.admin import register_admin, register_admin_extended
from callbacks.contrib import register_contrib
from callbacks.menu import register_menu
from callbacks.navigation import register_navigation

def register_all(registry):
    register_admin(registry)
    register_admin_extended(registry)
    register_contrib(registry)
    register_menu(registry)
    register_navigation(registry)
    _register_buy(registry)


def _register_buy(registry) -> None:
    from telegram.ext import ContextTypes
    from telegram import Update

    @registry.register("buy")
    async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        from handlers import handle_buy_callback
        await handle_buy_callback(update, context, f"pack_{payload}" if not payload.startswith("pack_") else payload)
