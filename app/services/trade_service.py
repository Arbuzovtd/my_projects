import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import async_session
from app.db.models import TradePosition, TradeFill, PositionStatus

logger = logging.getLogger(__name__)

class TradeService:
    async def get_active_position(self, symbol: str) -> TradePosition:
        async with async_session() as session:
            result = await session.execute(
                select(TradePosition)
                .where(TradePosition.symbol == symbol, TradePosition.status == PositionStatus.ACTIVE)
                .options(selectinload(TradePosition.fills))
            )
            return result.scalar_one_or_none()

    async def record_entry(self, symbol: str, side: str, price: float, quantity: float, order_id: str = None):
        """
        Records a new entry or averaging for a position.
        Calculates new average price.
        """
        async with async_session() as session:
            async with session.begin():
                # Try to find existing active position
                result = await session.execute(
                    select(TradePosition)
                    .where(TradePosition.symbol == symbol, TradePosition.status == PositionStatus.ACTIVE)
                    .options(selectinload(TradePosition.fills))
                )
                position = result.scalar_one_or_none()
                
                if not position:
                    # Create new position
                    position = TradePosition(
                        symbol=symbol,
                        side=side,
                        status=PositionStatus.ACTIVE,
                        total_quantity=quantity,
                        average_entry_price=price,
                        entry_time=datetime.utcnow()
                    )
                    session.add(position)
                    await session.flush() # Get ID
                    logger.info(f"DB: Created new {side} position for {symbol}")
                else:
                    # Average up/down
                    old_total = position.total_quantity
                    old_avg = position.average_entry_price
                    new_total = old_total + quantity
                    
                    # Weighted average: (Q1*P1 + Q2*P2) / (Q1 + Q2)
                    new_avg = ((old_total * old_avg) + (quantity * price)) / new_total
                    
                    position.total_quantity = new_total
                    position.average_entry_price = new_avg
                    logger.info(f"DB: Averaged {side} position for {symbol}: qty={new_total}, avg_price={new_avg}")

                # Record the fill
                fill = TradeFill(
                    position_id=position.id,
                    symbol=symbol,
                    side="buy" if side == "long" else "sell",
                    price=price,
                    quantity=quantity,
                    order_id=order_id
                )
                session.add(fill)
                
            await session.commit()
            return position

    async def record_close(self, symbol: str, exit_price: float, exit_reason: str = "exit_signal"):
        """
        Closes the active position and calculates final PnL.
        """
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(TradePosition)
                    .where(TradePosition.symbol == symbol, TradePosition.status == PositionStatus.ACTIVE)
                )
                position = result.scalar_one_or_none()
                
                if not position:
                    logger.warning(f"DB: No active position found to close for {symbol}")
                    return None
                
                # Calculate PnL
                # Long: (Exit - Entry) * Qty
                # Short: (Entry - Exit) * Qty
                multiplier = 1 if position.side == "long" else -1
                pnl = (exit_price - position.average_entry_price) * position.total_quantity * multiplier
                
                position.status = PositionStatus.CLOSED
                position.exit_price = exit_price
                position.exit_time = datetime.utcnow()
                position.total_pnl_usdt = pnl
                position.exit_reason = exit_reason
                
                logger.info(f"DB: Closed {position.side} position for {symbol}. PnL: {pnl:.2f} USDT")
                
            await session.commit()
            return position

trade_service = TradeService()
