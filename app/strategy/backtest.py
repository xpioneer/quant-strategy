import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base import BaseStrategy

class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 100_000.0,
        slippage: float = 0.0001,
        risk_free_rate: float = 0.025  # 年化无风险利率2.5%
    ):
        self.initial_capital = initial_capital
        self.slippage = slippage
        self.risk_free_rate = risk_free_rate

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, commission: float = 0.0003) -> Dict[str, Any]:
        # 时间排序、拷贝隔离原数据
        df = df.copy().sort_values("date").reset_index(drop=True)
        signals = strategy.generate_signals(df)
        df["signal"] = signals

        cash = self.initial_capital
        position = 0  # 持仓股数，0=空仓
        trades: List[Dict] = []
        equity: List[Dict] = []
        total_days = len(df)

        for i, row in enumerate(df.itertuples()):
            # 1. 每日先记录当日资产（所有日期都记录，不丢失尾部净值）
            portfolio_value = cash + position * row.close
            equity.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "portfolio_value": round(portfolio_value, 2),
                "cash": round(cash, 2),
                "position": position
            })

            # 最后一天无次日开盘，跳过交易执行
            if i >= total_days - 1:
                break
            next_row = df.iloc[i + 1]
            exec_price = float(next_row.open)

            # ===== 交易逻辑：增加持仓状态判断，禁止重复买卖 =====
            # 买入：空仓 + 信号1
            if row.signal == 1 and cash > 0 and position == 0:
                cost_rate = 1 + commission + self.slippage
                cost_per_share = exec_price * cost_rate
                shares = int(cash // cost_per_share)
                if shares > 0:
                    total_cost = shares * cost_per_share
                    cash -= total_cost
                    position += shares
                    trades.append({
                        "date": next_row.date.strftime("%Y-%m-%d"),
                        "type": "buy",
                        "exec_price": round(exec_price, 2),
                        "shares": shares,
                        "total_cost": round(total_cost, 2)
                    })

            # 卖出：持仓 + 信号-1
            elif row.signal == -1 and position > 0:
                revenue_rate = 1 - commission - self.slippage
                total_revenue = position * exec_price * revenue_rate
                cash += total_revenue
                trades.append({
                    "date": next_row.date.strftime("%Y-%m-%d"),
                    "type": "sell",
                    "exec_price": round(exec_price, 2),
                    "shares": position,
                    "total_revenue": round(total_revenue, 2)
                })
                position = 0

        # ========== 向量化绩效计算 ==========
        eq_df = pd.DataFrame(equity)
        final_value = eq_df["portfolio_value"].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        # 日收益率，空值兜底
        rets = eq_df["portfolio_value"].pct_change().dropna()
        annual_sharpe = 0.0
        if len(rets) > 0 and rets.std() > 1e-8:
            annual_ret = rets.mean() * 252
            annual_vol = rets.std() * np.sqrt(252)
            annual_sharpe = (annual_ret - self.risk_free_rate) / annual_vol

        # 最大回撤
        rolling_max = eq_df["portfolio_value"].cummax()
        drawdown = (eq_df["portfolio_value"] - rolling_max) / rolling_max
        max_dd_pct = abs(drawdown.min()) * 100 if not drawdown.empty else 0.0

        return {
            "initial_capital": round(self.initial_capital, 2),
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(annual_sharpe, 2),
            "max_drawdown": round(max_dd_pct, 2),
            "total_trades": len(trades),
            "trade_list": trades,        # 完整交易记录，入库/表格展示
            "equity_curve": equity       # 净值曲线，ECharts绘图
        }