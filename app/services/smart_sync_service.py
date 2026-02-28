import logging
from typing import Optional
from app.models.webhook_signal import WebhookSignal
from app.services.exchange_service import exchange_service
from app.services.config_service import config_service
from app.services.telegram_service import send_message

logger = logging.getLogger(__name__)

class SmartSyncService:
    async def process_signal(self, signal: WebhookSignal):
        symbol = signal.ticker
        config = await config_service.get_config()
        symbol_config = config.root.get(symbol)
        
        if not symbol_config:
            msg = f"⚠️ Symbol {symbol} not found in config. Ignoring signal."
            logger.warning(msg)
            await send_message(msg)
            return {"status": "ignored", "reason": f"Symbol {symbol} not in config"}
        
        if symbol_config.status == "paused":
            logger.info(f"Symbol {symbol} is paused. Ignoring signal.")
            return {"status": "ignored", "reason": "Paused"}
        
        if signal.action == "entry":
            return await self._handle_entry(signal, symbol_config.multiplier)
        elif signal.action == "close_all":
            return await self._handle_close_all(signal)
        
        return {"status": "error", "reason": "Unknown action"}

    async def _handle_entry(self, signal: WebhookSignal, multiplier: float):
        symbol = signal.ticker
        side = "buy" if signal.side == "long" else "sell"
        qty = signal.qty * multiplier
        
        if qty <= 0:
            logger.warning(f"Calculated quantity is {qty} for {symbol}. Ignoring.")
            return {"status": "ignored", "reason": "Zero quantity"}

        logger.info(f"CCXT: Placing entry order for {symbol}: side={side}, qty={qty}")
        
        response = await exchange_service.create_market_order(
            symbol=symbol,
            side=side,
            amount=qty
        )
        
        if response.get("retCode") == 0:
            order_data = response.get("result", {})
            logger.info(f"CCXT: Order placed successfully: {order_data.get('id')}")
            await send_message(f"✅ Order placed for {symbol}: {side} {qty}")
            return {"status": "success", "order_id": order_data.get('id')}
        else:
            reason = response.get("retMsg")
            logger.error(f"CCXT: Failed to place order: {reason}")
            await send_message(f"❌ Failed to place order for {symbol}: {reason}")
            return {"status": "error", "reason": reason}

    async def _handle_close_all(self, signal: WebhookSignal):
        symbol = signal.ticker
        positions_response = await exchange_service.get_positions(symbol=symbol)
        
        if positions_response.get("retCode") != 0:
            reason = positions_response.get("retMsg")
            logger.error(f"CCXT: Failed to get positions: {reason}")
            await send_message(f"❌ Failed to get positions for {symbol}: {reason}")
            return {"status": "error", "reason": reason}
        
        results = []
        positions = positions_response.get("result", {}).get("list", [])
        
        for pos in positions:
            # CCXT position structure: 'side' is 'long'/'short', 'contracts' is size
            pos_side = pos.get("side") # 'long' or 'short'
            pos_size = float(pos.get("contracts", 0))
            
            if pos_size == 0:
                continue
            
            # Match signal side to position side
            should_close = (
                (signal.side == "long" and pos_side == "long") or
                (signal.side == "short" and pos_side == "short")
            )
            
            if should_close:
                # Opposite side to close
                close_side = "sell" if pos_side == "long" else "buy"
                logger.info(f"CCXT: Closing position for {symbol}: {pos_side} {pos_size}")
                
                resp = await exchange_service.create_market_order(
                    symbol=symbol,
                    side=close_side,
                    amount=pos_size,
                    params={"reduceOnly": True}
                )
                results.append(resp)
                
                if resp.get("retCode") == 0:
                    await send_message(f"✅ Position closed for {symbol}: {pos_side} {pos_size}")
                else:
                    await send_message(f"❌ Failed to close {pos_side} position for {symbol}: {resp.get('retMsg')}")
        
        if not results:
            logger.info(f"CCXT: No open {signal.side} positions found to close for {symbol}")
            return {"status": "success", "message": "No positions to close"}
        
        return {"status": "success", "results": results}

smart_sync_service = SmartSyncService()
