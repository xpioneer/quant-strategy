# app/strategy/backtest.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base import BaseStrategy


class BacktestEngine:
    def __init__(self, initial_capital: float = 100_000.0):
        self.initial_capital = initial_capital

    def run(
        self,
        df: pd.DataFrame,
        strategy: BaseStrategy,
        commission: float = 0.0003,
    ) -> Dict[str, Any]:
        df = df.copy().sort_values("date").reset_index(drop=True)

        signals = strategy.generate_signals(df)

        cash = self.initial_capital
        position = 0          # ★ 当天持仓股数
        buy_price = None      # 记录最后一次买入价（用于止损等）
        trades: List[Dict] = []
        equity: List[Dict] = []

        for i in range(len(df)):
            sig = signals.iloc[i]
            price = float(df.at[i, "close"])
            date = df.at[i, "date"]

            # ---- 执行交易 ----
            if sig == 1 and cash > 0:          # 买入
                shares = int(cash // (price * (1 + commission)))
                if shares > 0:
                    cost = shares * price * (1 + commission)
                    cash -= cost
                    position += shares
                    buy_price = price
                    trades.append({
                        "date": date,
                        "type": "buy",
                        "price": price,
                        "shares": shares,
                        "cost": round(cost, 2),
                        "cash_after": round(cash, 2),
                    })

            elif sig == -1 and position > 0:   # 卖出
                revenue = position * price * (1 - commission)
                cash += revenue
                trades.append({
                    "date": date,
                    "type": "sell",
                    "price": price,
                    "shares": position,
                    "revenue": round(revenue, 2),
                    "cash_after": round(cash, 2),
                })
                position = 0
                buy_price = None

            # ★★★ 关键：用【当天真实 cash 和 position】算资产 ★★★
            portfolio_value = round(cash + position * price, 2)
            equity.append({
                "date": date,
                "portfolio_value": portfolio_value,
                "cash": round(cash, 2),
                "position": position,
            })

        # ---- 绩效 ----
        final_value = equity[-1]["portfolio_value"]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        # 日收益率
        rets = []
        for j in range(1, len(equity)):
            prev = equity[j - 1]["portfolio_value"]
            cur = equity[j]["portfolio_value"]
            rets.append((cur - prev) / prev if prev else 0)
        rets = np.array(rets)
        sharpe = 0.0
        if rets.std() > 0:
            sharpe = round(np.sqrt(252) * rets.mean() / rets.std(), 2)

        # 最大回撤
        peak = equity[0]["portfolio_value"]
        max_dd = 0.0
        for v in equity:
            pv = v["portfolio_value"]
            if pv > peak:
                peak = pv
            dd = (peak - pv) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 2),
            "sharpe_ratio": sharpe,
            "max_drawdown": round(max_dd, 2),
            "total_trades": sum(1 for t in trades if t["type"] == "buy"),
            "trades": trades,
            "equity_curve": equity,
        }