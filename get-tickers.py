import os

import pandas as pd
import psycopg2
import yfinance as yf
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "JPM", "NVDA", "JNJ"]
start_date = "2026-01-01"
table_name = "stock_prices_vsc"
file_name = "stock_prices.csv"

def get_connection():
    return psycopg2.connect(os.environ["neon_connection_string"])

def fetch_prices():
    # daily adjusted closing prices for all tickers, in long format
    data = yf.download(tickers, start=start_date, auto_adjust=True)
    if data.empty:
        raise RuntimeError("yfinance returned no data")
    df = (data["Close"]
        .reset_index()
        .melt(id_vars="Date", var_name="ticker", value_name="close_price")
        .rename(columns={"Date": "price_date"})
        .dropna(subset=["close_price"])
        .sort_values(by=["ticker", "price_date"])
    )
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date
    df["close_price"] = df["close_price"].round(4)   # removes floating-point noise
    return df.reset_index(drop=True)

def create_table():
    # make the table if it doesn't exist yet
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"""
            create table if not exists {table_name} (
                price_date  date    not null,
                ticker      text    not null,
                close_price numeric not null,
                primary key (price_date, ticker)
            )
        """)

def load_existing():
    # read the table from Neon, or return None if it's empty
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"select price_date, ticker, close_price from {table_name}")
        rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["price_date", "ticker", "close_price"])
    df["close_price"] = df["close_price"].astype(float)   # Postgres numeric -> float
    return df

def get_changes(df, existing):
    # keep only rows that are new, or whose price changed
    if existing is None:
        return df   # empty table: everything is new
    merged = df.merge(
        existing, on=["price_date", "ticker"], how="left", suffixes=("", "_old")
    )
    is_new = merged["close_price_old"].isna()
    changed = (merged["close_price"] - merged["close_price_old"]).abs() > 5e-5
    return merged.loc[is_new | changed, ["price_date", "ticker", "close_price"]]

def save_to_neon(df):
    # upsert: new rows are inserted, existing rows are updated
    rows = [
        (row.price_date, row.ticker, float(row.close_price))
        for row in df.itertuples(index=False)
    ]
    with get_connection() as conn, conn.cursor() as cur:
        execute_values(cur, f"""
            insert into {table_name} (price_date, ticker, close_price)
            values %s
            on conflict (price_date, ticker) do update
            set close_price = excluded.close_price
        """, rows)
    print(f"Neon: upserted {len(rows)} row(s) into {table_name}")

def save_csv(df):
    # local copy of the full dataset
    df.to_csv(file_name, index=False)
    print(f"CSV: saved {len(df)} rows to {file_name}")

def main():
    df = fetch_prices()
    create_table()
    existing = load_existing()

    changes = get_changes(df, existing)
    if changes.empty:
        print("Neon: nothing new to save")
    else:
        save_to_neon(changes)

    save_csv(df)   # full dataset

if __name__ == "__main__":
    main()