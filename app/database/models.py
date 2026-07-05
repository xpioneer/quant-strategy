from sqlalchemy import Column, String, DateTime, Float, Integer, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    symbol = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    market = Column(String)
    list_date = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Kline(Base):
    __tablename__ = "klines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    amplitude = Column(Float)
    pct_change = Column(Float)
    change = Column(Float)
    turnover_rate = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    strategy_type = Column(String)
    parameters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
