import yfinance as yf

tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "JPM", "NVDA", "JNJ"]
data = yf.download(tickers, start="2026-01-01", auto_adjust=True)
df = (data["Close"]
    .reset_index()
    .melt(id_vars="Date", var_name="ticker", value_name="close_price")
    .sort_values(by=["ticker", "Date"])
)

df.to_csv("stock_prices.csv", index=False)
print(df.head())
print(f"Saved {len(df)} rows to stock_prices.csv")