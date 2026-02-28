from pydantic import ValidationError
import pytest
from app.models.webhook_signal import WebhookSignal

def test_valid_entry_signal():
    data = {
        "passphrase": "test_secret",
        "ticker": "BTCUSDT",
        "action": "entry",
        "side": "long",
        "qty": 1.5
    }
    signal = WebhookSignal(**data)
    assert signal.passphrase == "test_secret"
    assert signal.ticker == "BTCUSDT"
    assert signal.action == "entry"
    assert signal.side == "long"
    assert signal.qty == 1.5

def test_valid_close_all_signal():
    data = {
        "passphrase": "test_secret",
        "ticker": "ETHUSDT",
        "action": "close_all",
        "side": "short",
        "qty": 0.0
    }
    signal = WebhookSignal(**data)
    assert signal.action == "close_all"

def test_invalid_action():
    data = {
        "passphrase": "test_secret",
        "ticker": "BTCUSDT",
        "action": "invalid_action",
        "side": "long",
        "qty": 1.0
    }
    with pytest.raises(ValidationError):
        WebhookSignal(**data)

def test_invalid_side():
    data = {
        "passphrase": "test_secret",
        "ticker": "BTCUSDT",
        "action": "entry",
        "side": "neutral",
        "qty": 1.0
    }
    with pytest.raises(ValidationError):
        WebhookSignal(**data)

def test_missing_field():
    data = {
        "ticker": "BTCUSDT",
        "action": "entry",
        "side": "long",
        "qty": 1.0
    }
    with pytest.raises(ValidationError):
        WebhookSignal(**data)
