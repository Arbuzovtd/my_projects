import asyncio
import logging
from app.services.bybit_service import bybit_client
from app.core.logging_config import setup_logging

async def main():
    setup_logging()
    print("Testing Bybit connectivity...")
    # Try to get balance - simplest check
    balance = await bybit_client.get_wallet_balance()
    print(f"Balance response: {balance}")
    
    # Try to place a small test order if balance is OK (optional, let's just check balance first)

if __name__ == "__main__":
    asyncio.run(main())
