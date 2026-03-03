import logging
from typing import Optional
from app.models.webhook_signal import WebhookSignal
from app.services.exchange_service import exchange_service
from app.services.config_service import config_service
from app.services.trade_service import trade_service
from app.services.telegram_service import send_message

logger = logging.getLogger(__name__)

class SmartSyncService:
    async def process_signal(self, signal: WebhookSignal):
        symbol = signal.ticker
        config = await config_service.get_config()
        symbol_config = config.symbols.get(symbol)
        
        if not symbol_config:
            msg = f"⚠️ Symbol {symbol} not found in config. Ignoring signal."
            logger.warning(msg)
            await send_message(msg)
            return {"status": "ignored", "reason": f"Symbol {symbol} not in config"}
        
        if symbol_config.status == "paused":
            logger.info(f"Symbol {symbol} is paused. Ignoring signal.")
            return {"status": "ignored", "reason": "Paused"}
        
        if signal.action == "entry":
            return await self._handle_entry(signal, symbol_config.multiplier, symbol_config.leverage)
        elif signal.action == "close_all":
            return await self._handle_close_all(signal)
        
        return {"status": "error", "reason": "Unknown action"}

    async def _handle_entry(self, signal: WebhookSignal, multiplier: float, leverage: int):
        symbol = signal.ticker
        side = "buy" if signal.side == "long" else "sell"
        qty = signal.qty * multiplier
        
        if qty <= 0:
            logger.warning(f"Calculated quantity is {qty} for {symbol}. Ignoring.")
            return {"status": "ignored", "reason": "Zero quantity"}

        # Set leverage first
        await exchange_service.set_leverage(symbol, leverage)

        logger.info(f"CCXT: Placing entry order for {symbol}: side={side}, qty={qty}")
        
        response = await exchange_service.create_market_order(
            symbol=symbol,
            side=side,
            amount=qty,
            params={"recvWindow": 60000}
        )
        
        if response.get("retCode") == 0:
            order_data = response.get("result", {})
            order_id = order_data.get('id')
            
            # Get current price to record in DB (or price from order if available)
            # Market orders usually return 'price' as None or 0 in some exchanges until filled
            execution_price = order_data.get('price') or order_data.get('average')
            
            if not execution_price:
                ticker = await exchange_service.get_ticker(symbol)
                execution_price = ticker.get('last') if ticker else 0

            # Record in Database
            await trade_service.record_entry(
                symbol=symbol,
                side=signal.side,
                price=execution_price,
                quantity=qty,
                order_id=order_id
            )

            logger.info(f"CCXT: Order placed successfully: {order_id} at {execution_price}")
            await send_message(f"✅ Order placed for {symbol}: {side} {qty} @ {execution_price}")
            return {"status": "success", "order_id": order_id}
        else:
            reason = response.get("retMsg")
            logger.error(f"CCXT: Failed to place order: {reason}")
            await send_message(f"❌ Failed to place order for {symbol}: {reason}")
            return {"status": "error", "reason": reason}

    async def _handle_close_all(self, signal: WebhookSignal):
        symbol = signal.ticker
        
        # 1. Check our database first for active position
        position = await trade_service.get_active_position(symbol)
        
        if not position:
            msg = f"ℹ️ No active position for {symbol} found in DB. Nothing to close."
            logger.info(msg)
            # Optional: Fallback to exchange check if you want to be extra sure
            # But according to user request, we want to avoid "close all" by mistake.
            return {"status": "success", "message": "No tracked position found"}

        # 2. Match signal side to position side
        if signal.side != position.side:
            logger.warning(f"Close signal for {signal.side} but DB says position is {position.side}. Ignoring.")
            return {"status": "ignored", "reason": "Side mismatch"}

        # 3. Close the tracked quantity
        close_side = "sell" if position.side == "long" else "buy"
        pos_size = position.total_quantity
        
        logger.info(f"CCXT: Closing tracked position for {symbol}: {position.side} {pos_size}")
        
        resp = await exchange_service.create_market_order(
            symbol=symbol,
            side=close_side,
            amount=pos_size,
            params={"reduceOnly": True, "recvWindow": 60000}
        )
        
        if resp.get("retCode") == 0:
            order_data = resp.get("result", {})
            exit_price = order_data.get('price') or order_data.get('average')
            
            if not exit_price:
                ticker = await exchange_service.get_ticker(symbol)
                exit_price = ticker.get('last') if ticker else 0
                
            # Update Database
            closed_pos = await trade_service.record_close(
                symbol=symbol,
                exit_price=exit_price,
                exit_reason="exit_signal"
            )
            
            pnl_msg = f" (PnL: {closed_pos.total_pnl_usdt:.2f} USDT)" if closed_pos else ""
            await send_message(f"✅ Position closed for {symbol}: {position.side} {pos_size} @ {exit_price}{pnl_msg}")
            return {"status": "success", "pnl": closed_pos.total_pnl_usdt if closed_pos else 0}
        else:
            reason = resp.get("retMsg")
            logger.error(f"❌ Failed to close {position.side} position for {symbol}: {reason}")
            await send_message(f"❌ Failed to close position for {symbol}: {reason}")
            return {"status": "error", "reason": reason}

smart_sync_service = SmartSyncService()
