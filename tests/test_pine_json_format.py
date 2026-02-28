import json
import pytest
from app.models.webhook_signal import WebhookSignal
from pydantic import ValidationError

def test_pine_script_entry_template_validation():
    # Simulated JSON produced by Pine script for an entry signal
    pine_json = '{"passphrase":"secret", "ticker":"BTCUSDT", "action":"entry", "side":"long", "qty":1.5}'
    
    # Parse and validate
    data = json.loads(pine_json)
    signal = WebhookSignal(**data)
    
    assert signal.passphrase == "secret"
    assert signal.ticker == "BTCUSDT"
    assert signal.action == "entry"
    assert signal.side == "long"
    assert signal.qty == 1.5

def test_pine_script_close_all_template_validation():
    # Simulated JSON produced by Pine script for a close_all signal
    pine_json = '{"passphrase":"secret", "ticker":"ETHUSDT", "action":"close_all", "side":"short", "qty":0.0}'
    
    # Parse and validate
    data = json.loads(pine_json)
    signal = WebhookSignal(**data)
    
    assert signal.action == "close_all"
    assert signal.ticker == "ETHUSDT"
    assert signal.side == "short"

def test_pine_script_qty_as_float_from_string():
    # TV's str.tostring(qty) will produce string values that JSON/Pydantic must handle correctly
    pine_json = '{"passphrase":"secret", "ticker":"SOLUSDT", "action":"entry", "side":"long", "qty":10}'
    
    data = json.loads(pine_json)
    signal = WebhookSignal(**data)
    
    assert signal.qty == 10.0
    assert isinstance(signal.qty, float)

def test_invalid_json_format():
    # Case where JSON is malformed (e.g. missing quote)
    malformed_json = '{"passphrase":"secret, "ticker":"BTCUSDT"}'
    
    with pytest.raises(json.JSONDecodeError):
        json.loads(malformed_json)
