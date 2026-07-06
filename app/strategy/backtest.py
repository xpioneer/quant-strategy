# app/strategy/backtest.py
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import BaseStrategy

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        
    def run(self, df: pd.DataFrame, strategy: BaseStrategy, 
            commission: float = 0.0003) -> Dict[str, Any]:
        """
        执行回测
        df: 包含 date, open, high, low, close, volume 的 DataFrame
        strategy: 策略实例
        commission: 手续费率 (默认万三)
        """
        df = df.copy().sort_values("date").reset_index(drop=True)
        
        # 生成信号
        signals = strategy.generate_signals(df)
        
        # 回测模拟
        capital = self.initial_capital
        position = 0  # 持仓数量
        cash = capital
        trades = []   # 交易记录
        
        for i in range(len(df)):
            signal = signals.iloc[i]
            price = df.iloc[i]["close"]
            date = df.iloc[i]["date"]
            
            if signal == 1 and cash > 0:  # 买入
                shares = cash // (price * (1 + commission))
                cost = shares * price * (1 + commission)
                cash -= cost
                position += shares
                trades.append({
                    "date": date,
                    "type": "buy",
                    "price": price,
                    "shares": shares,
                    "cost": cost,
                    "cash_after": cash
                })
                
            elif signal == -1 and position > 0:  # 卖出
                revenue = position * price * (1 - commission)
                cash += revenue
                trades.append({
                    "date": date,
                    "type": "sell",
                    "price": price,
                    "shares": position,
                    "revenue": revenue,
                    "cash_after": cash
                })
                position = 0
        
        # 计算绩效
        final_value = cash + position * df.iloc[-1]["close"]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 计算每日收益率（用于夏普比率等）
        df["portfolio_value"] = cash + position * df["close"]
        df["daily_return"] = df["portfolio_value"].pct_change()
        
        sharpe = np.sqrt(252) * df["daily_return"].mean() / df["daily_return"].std() if df["daily_return"].std() > 0 else 0
        max_drawdown = (df["portfolio_value"].cummax() - df["portfolio_value"]).max() / df["portfolio_value"].cummax().max() * 100
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_trades": len([t for t in trades if t["type"] == "buy"]),
            "trades": trades,
            "equity_curve": df[["date", "portfolio_value"]].to_dict("records")
        }