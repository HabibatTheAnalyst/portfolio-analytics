import numpy as np
import pandas as pd

prices = pd.read_csv("stock_prices.csv", parse_dates=["Date"])
rng = np.random.default_rng(42)  # fixed seed so you get the same file every run

# (planned date, ticker, shares)
plan = [
    ("2026-01-05", "AAPL", 20),
    ("2026-01-05", "MSFT", 10),
    ("2026-01-06", "NVDA", 25),
    ("2026-01-12", "JPM", 15),
    ("2026-01-20", "GOOGL", 15),
    ("2026-01-26", "AMZN", 20),
    ("2026-01-02", "TSLA", 10),
    ("2026-01-09", "JNJ", 18)
]

rows = []
for planned_date, ticker, shares in plan:
    match = prices[(prices["ticker"] == ticker) & (prices["Date"] >= planned_date)].iloc[0]
    price_paid = round(match["close_price"] * rng.uniform(0.995, 1.005), 2)
    rows.append({
        "date": match["Date"].strftime("%Y-%m-%d"),
        "ticker": ticker,
        "shares": shares,
        "price_paid": price_paid,
    })

trades = pd.DataFrame(rows).sort_values("date")
trades.to_csv("trade_log.csv", index=False)
# print(trades)