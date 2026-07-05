from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.models import Stock, Kline, Strategy


class StockRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Stock]:
        return self.db.query(Stock).all()

    def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        return self.db.query(Stock).filter(Stock.symbol == symbol).first()

    def create(self, stock: Stock) -> Stock:
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)
        return stock


class KlineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_symbol(self, symbol: str) -> List[Kline]:
        return self.db.query(Kline).filter(Kline.symbol == symbol).order_by(Kline.date).all()


class StrategyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Strategy]:
        return self.db.query(Strategy).all()

    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        return self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
