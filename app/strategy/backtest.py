# app/strategy/backtest.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
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
        
        # ===== 逐日模拟交易 =====
        cash = self.initial_capital
        position = 0  # 持仓数量
        trades = []   # 交易记录
        daily_values = []  # 每日资产记录
        
        for i in range(len(df)):
            signal = signals.iloc[i]
            price = df.iloc[i]["close"]
            date = df.iloc[i]["date"]
            
            # 处理交易信号
            if signal == 1 and cash > 0:  # 买入
                shares = int(cash // (price * (1 + commission)))
                cost = round(shares * price * (1 + commission), 2)
                cash -= cost
                position += shares
                trades.append({
                    "date": date,
                    "type": "buy",
                    "price": price,
                    "shares": shares,
                    "cost": cost,
                    "cash_after": round(cash, 2)
                })
                
            elif signal == -1 and position > 0:  # 卖出
                revenue = round(position * price * (1 - commission), 2)
                cash += revenue
                trades.append({
                    "date": date,
                    "type": "sell",
                    "price": price,
                    "shares": position,
                    "revenue": revenue,
                    "cash_after": round(cash, 2)
                })
                position = 0
            
            # ===== ★ 关键修复：每天计算真实资产价值 =====
            portfolio_value = round(cash + position * price, 2)
            daily_values.append({
                "date": date,
                "portfolio_value": portfolio_value,
                "cash": round(cash, 2),
                "position": position,
                "price": price
            })
        
        # 计算绩效
        final_value = daily_values[-1]["portfolio_value"]
        total_return = round((final_value - self.initial_capital) / self.initial_capital * 100, 2)
        
        # 计算每日收益率（用于夏普比率）
        returns = []
        for j in range(1, len(daily_values)):
            prev_val = daily_values[j-1]["portfolio_value"]
            curr_val = daily_values[j]["portfolio_value"]
            if prev_val > 0:
                returns.append((curr_val - prev_val) / prev_val)
            else:
                returns.append(0)
        
        daily_returns = np.array(returns)
        sharpe = 0
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            sharpe = round(np.sqrt(252) * daily_returns.mean() / daily_returns.std(), 2)
        
        # 计算最大回撤
        values = [v["portfolio_value"] for v in daily_values]
        peak = values[0]
        max_drawdown = 0
        for v in values:
            if v > peak:
                peak = v
            drawdown = round((peak - v) / peak * 100, 2)
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_trades": len([t for t in trades if t["type"] == "buy"]),
            "trades": trades,
            "equity_curve": daily_values
        }