import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

table_name = "company_vsc"
file_name = "company.csv"

companies = [
    ("AAPL",  "Apple",             "Consumer tech"),
    ("MSFT",  "Microsoft",         "Software"),
    ("GOOGL", "Alphabet",          "Internet"),
    ("AMZN",  "Amazon",            "E-commerce"),
    ("NVDA",  "Nvidia",            "Semiconductors"),
    ("JPM",   "JPMorgan Chase",    "Banking"),
    ("TSLA",  "Tesla",             "Automotive"),
    ("JNJ",   "Johnson & Johnson", "Healthcare"),
]

def get_connection():
    return psycopg2.connect(os.environ["neon_connection_string"])

def build_dataset():
    df = pd.DataFrame(companies, columns=["ticker", "company_name", "sector"])
    df["ticker"] = df["ticker"].str.strip().str.upper()
    if df["ticker"].duplicated().any():
        raise ValueError("Duplicate tickers in the companies list")
    return df.sort_values("ticker").reset_index(drop=True)

def create_table():
    # make the table if it doesn't exist yet
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"""
            create table if not exists {table_name} (
                ticker       text primary key,
                company_name text not null,
                sector       text not null
            )
        """)

def save_to_neon(df):
    # upsert: new tickers are inserted, existing ones are updated
    rows = list(df.itertuples(index=False, name=None))
    with get_connection() as conn, conn.cursor() as cur:
        execute_values(cur, f"""
            insert into {table_name} (ticker, company_name, sector)
            values %s
            on conflict (ticker) do update
            set company_name = excluded.company_name,
                sector       = excluded.sector
        """, rows)
    print(f"Neon: upserted {len(rows)} rows into {table_name}")

def save_csv(df):
    df.to_csv(file_name, index=False)
    print(f"CSV: saved {len(df)} rows to {file_name}")

def main():
    df = build_dataset()
    create_table()
    save_to_neon(df)
    save_csv(df)

if __name__ == "__main__":
    main()