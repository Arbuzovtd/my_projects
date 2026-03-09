import pytest
from unittest.mock import MagicMock, patch

# This file will be loaded by pytest before any test collection
# We patch aiogram.Bot globally to avoid TokenValidationError during test collection
# when importing modules that initialize the bot.

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    patcher = patch("aiogram.Bot")
    patcher.start()
    session.config.bot_patcher = patcher

def pytest_sessionfinish(session, exitstatus):
    if hasattr(session.config, "bot_patcher"):
        session.config.bot_patcher.stop()
