import akshare as ak
df = ak.stock_zh_a_hist(
  symbol="sh000001",   # 上证指数，测试用
  start_date="20250101",
  end_date="20250706",
  adjust="qfq"
)
print(df.tail())