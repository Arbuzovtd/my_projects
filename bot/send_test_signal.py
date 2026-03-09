import requests
import json
import sys

def send_signal(action, ticker, side, qty=1.0):
    url = "http://localhost:8000/webhook"
    payload = {
        "passphrase": "default_secret", # Change if you updated it in .env
        "ticker": ticker,
        "action": action, # 'entry' or 'close_all'
        "side": side,     # 'long' or 'short'
        "qty": qty
    }
    
    print(f"Sending {action} signal for {ticker} ({side})...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python send_test_signal.py <action> <ticker> <side> [qty]")
        print("Example: python send_test_signal.py entry BTCUSDT long 0.01")
        sys.exit(1)
    
    action = sys.argv[1]
    ticker = sys.argv[2]
    side = sys.argv[3]
    qty = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    
    send_signal(action, ticker, side, qty)
