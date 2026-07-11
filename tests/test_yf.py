import yfinance as yf

df = yf.download(
    "NVDA",
    start="2020-01-01",
    end="2025-01-01",
    auto_adjust=True
)

print(df.head())