import backtrader as bt
import pandas as pd

class TradeRecorder(bt.Analyzer):
    """记录每日持仓明细，包含日期、现金、持仓市值、总资产、操作类型"""

    def start(self):
        self.trades = []

    def notify_cashvalue(self, cash, value):
        record = {
            'date': self.datas[0].datetime.date(0).isoformat(),
            'cash': round(cash, 2),
            'holdings': round(value - cash, 2),
            'total': round(value, 2),
            'action': 'hold',
            'price': 0,
            'size': 0,
        }
        self.trades.append(record)

    def notify_order(self, order):
        if order.status == order.Completed:
            if self.trades:
                last = self.trades[-1]
                if order.isbuy():
                    last['action'] = 'buy'
                else:
                    last['action'] = 'sell'
                last['price'] = round(order.executed.price, 2)
                last['size'] = order.executed.size

    def get_analysis(self):
        return {'trades': self.trades}

class ValueRecorder(bt.Analyzer):
    """记录每日净值"""
    def start(self):
        self.values = []
    def notify_cashvalue(self, cash, value):
        self.values.append(value)
    def get_analysis(self):
        return {'values': self.values}


class BacktraderEngine:
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital

    def run_strategy(self, df: pd.DataFrame, strategy_class, **params):
        cerebro = bt.Cerebro()
        
        # 1. 加载数据
        data = bt.feeds.PandasData(
            dataname=df, 
            datetime='date', 
            open='open', 
            high='high', 
            low='low', 
            close='close', 
            volume='volume'
        )
        cerebro.adddata(data)
        
        # 2. 添加策略
        cerebro.addstrategy(strategy_class, **params)
        
        # 3. 设置初始资金和手续费
        cerebro.broker.setcash(self.initial_capital)
        cerebro.broker.setcommission(commission=0.0003)
        
        # 4. 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades_stats')
        cerebro.addanalyzer(TradeRecorder, _name='trades')
        
        # 5. 运行
        print(f'初始资产: {self.initial_capital:.2f}')
        result = cerebro.run()
        strat = result[0]
        final_value = cerebro.broker.getvalue()
        print(f'最终资产: {final_value:.2f}')
        
        # 6. 提取分析结果
        trade_analysis = strat.analyzers.trades_stats.get_analysis()
        total_trades = trade_analysis.total.total if hasattr(trade_analysis, 'total') else 0
        
        analysis = {
            'initial_capital': self.initial_capital,
            'final_value': round(final_value, 2),
            'return_pct': round((final_value / self.initial_capital - 1) * 100, 2),
            'sharpe_ratio': round(strat.analyzers.sharpe.get_analysis().get('sharperatio', 0), 2),
            'max_drawdown_pct': round(strat.analyzers.drawdown.get_analysis().max.drawdown, 2),
            'total_trades': total_trades,
            'annual_return_pct': round(strat.analyzers.returns.get_analysis().get('rnorm100', 0), 2),
            'equity_curve': strat.analyzers.trades.get_analysis()['trades'],
        }
        
        return analysis