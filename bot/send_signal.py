import httpx
import asyncio

async def send_test_signal():
    url = "https://big-dots-change.loca.lt/webhook"
    payload = {
        "passphrase": "default_secret",
        "ticker": "BTCUSDT",
        "action": "entry",
        "side": "long",
        "qty": 0.01
    }
    
    print(f"Sending signal to {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_signal())
