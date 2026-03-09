import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class PositionStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class TradePosition(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False) # 'long' or 'short'
    status = Column(SAEnum(PositionStatus), default=PositionStatus.ACTIVE, index=True)
    
    # Aggregated data
    total_quantity = Column(Float, default=0.0)
    average_entry_price = Column(Float, default=0.0)
    
    # Entry/Exit info
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    
    # Financials
    total_pnl_usdt = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)

    # Relationships
    fills = relationship("TradeFill", back_populates="position", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position(id={self.id}, symbol={self.symbol}, status={self.status.value}, qty={self.total_quantity})>"

class TradeFill(Base):
    """
    Represents a single entry/averaging or partial exit order within a position.
    """
    __tablename__ = "trade_fills"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False) # 'buy' or 'sell'
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    order_id = Column(String, nullable=True)

    position = relationship("TradePosition", back_populates="fills")

    def __repr__(self):
        return f"<Fill(id={self.id}, side={self.side}, price={self.price}, qty={self.quantity})>"
