import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import psycopg2
import requests
import yfinance as yf
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

url = "https://open.er-api.com/v6/latest/USD"
table_name = "exchange_rates_vsc"
file_name = "exchange_rates.csv"
start_date = "2026-01-01"

def get_connection():
    return psycopg2.connect(os.environ["neon_connection_string"])

def fetch_today():
    # latest USD/NGN rate from the API
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("result") != "success":
        raise RuntimeError(f"API error: {data}")
    rate_date = datetime.fromtimestamp(
        data["time_last_update_unix"], tz=timezone.utc
    ).date()
    return pd.DataFrame([{
        "rate_date": rate_date,
        "usd_ngn_rate": float(data["rates"]["NGN"]),
    }])

def fetch_history(start_date):
    # daily USD/NGN rates from Yahoo, from start_date to today
    history_data = yf.Ticker("USDNGN=X").history(start=str(start_date), auto_adjust=True)
    if history_data.empty:
        return pd.DataFrame(columns=["rate_date", "usd_ngn_rate"])
    df = pd.DataFrame({
        "rate_date": history_data.index.tz_localize(None).date,
        "usd_ngn_rate": history_data["Close"].values,
    })
    return df.dropna()

def create_table():
    # make the table if it doesn't exist yet
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"""
            create table if not exists {table_name} (
                rate_date    date primary key,
                usd_ngn_rate numeric not null,
                is_filled    boolean not null default false
            )
        """)

def load_existing():
    # read the table from Neon, or return None if it's empty
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"select rate_date, usd_ngn_rate, is_filled from {table_name}")
        rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["rate_date", "usd_ngn_rate", "is_filled"])
    df["usd_ngn_rate"] = df["usd_ngn_rate"].astype(float)   # Postgres numeric -> float
    return df

def find_missing_weekdays(existing):
    # weekdays with no row, from the first date in the table up to yesterday (UTC)
    # today's rate is added separately by fetch_today()
    have = set(existing["rate_date"])
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    expected = pd.bdate_range(min(have), yesterday).date
    return sorted(d for d in expected if d not in have)

def fill_holidays(df):
    # carry the previous rate forward onto weekdays that have no data (possibly holidays)
    df = df.copy()
    df.index = pd.to_datetime(df["rate_date"])
    df = df.sort_index()
    all_days = df.index.union(pd.bdate_range(df.index.min(), df.index.max()))
    df = df.reindex(all_days)
    df["is_filled"] = df["usd_ngn_rate"].isna()
    df["usd_ngn_rate"] = df["usd_ngn_rate"].ffill()
    df["rate_date"] = df.index.date
    return df.reset_index(drop=True)[["rate_date", "usd_ngn_rate", "is_filled"]]

def collect_parts(existing):
    # decide what needs fetching and return the pieces to merge
    if existing is None:
        print("No data yet: running full backfill")
        return [fetch_history(start_date)]

    real = existing[~existing["is_filled"]]   # keep real rates only
    missing = find_missing_weekdays(existing)
    if missing:
        print(f"{len(missing)} weekday(s) missing, earliest {missing[0]}: filling")
        return [fetch_history(missing[0]), real]

    print("No gaps found")
    return [real]

def build_dataset(parts):
    # merge the pieces, keep one row per date (last wins), then fill holidays
    df = (pd.concat(parts)
            .drop_duplicates(subset="rate_date", keep="last")
            .sort_values("rate_date"))
    return fill_holidays(df)

def get_changes(df, existing):
    # keep only rows that are new, or whose rate / is_filled value changed
    if existing is None:
        return df   # empty table: everything is new

    merged = df.merge(
        existing, on="rate_date", how="left", suffixes=("", "_old")
    )
    is_new = merged["usd_ngn_rate_old"].isna()
    rate_changed = (merged["usd_ngn_rate"] - merged["usd_ngn_rate_old"]).abs() > 1e-9
    flag_changed = merged["is_filled"] != merged["is_filled_old"]

    return merged.loc[
        is_new | rate_changed | flag_changed,
        ["rate_date", "usd_ngn_rate", "is_filled"],
    ]

def save_to_neon(df):
    # upsert into Neon: new dates are inserted, existing dates are updated
    rows = [
        (row.rate_date, float(row.usd_ngn_rate), bool(row.is_filled))
        for row in df.itertuples(index=False)
    ]
    with get_connection() as conn, conn.cursor() as cur:
        execute_values(cur, f"""
            insert into {table_name} (rate_date, usd_ngn_rate, is_filled)
            values %s
            on conflict (rate_date) do update
            set usd_ngn_rate = excluded.usd_ngn_rate,
                is_filled    = excluded.is_filled
        """, rows)
    print(f"Neon: upserted {len(rows)} row(s), "
          f"{df['rate_date'].min()} to {df['rate_date'].max()}")

def save_csv(df):
    # local copy of the full dataset
    df.to_csv(file_name, index=False)
    print(f"CSV: saved {len(df)} rows ({int(df['is_filled'].sum())} filled) to {file_name}")

def main():
    create_table()
    existing = load_existing()
    parts = collect_parts(existing)
    parts.append(fetch_today())
    df = build_dataset(parts)

    changes = get_changes(df, existing)
    if changes.empty:
        print("Neon: nothing new to save")
    else:
        save_to_neon(changes)

    save_csv(df)   # full dataset

if __name__ == "__main__":
    main()