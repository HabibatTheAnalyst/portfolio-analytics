# Global Investment Analytics Platform

> **The question this answers:** *What is my investment portfolio actually worth, in both USD and Naira, over time?*

A personal portfolio data platform. Three different sources are ingested into a Neon (Postgres) warehouse, transformed with dbt Core into one analytics table, visualised in Metabase, and refreshed automatically every weekday by GitHub Actions.

![Dashboard](images/dashboardd.png)

---

## Architecture

```mermaid
flowchart LR
    subgraph Sources
        A["yfinance<br/>daily closing prices"]
        B["Google Sheet<br/>manual trade log"]
        C["apilayer API<br/>USD to NGN rates"]
        D["Company reference list"]
    end

    A -- Python --> N[("Neon Postgres<br/>raw tables")]
    C -- Python --> N
    D -- Python --> N
    B -- "Airbyte Cloud" --> N

    N --> T["dbt Core<br/>staging, intermediate, mart"]
    T --> M["Metabase in Docker<br/>dashboard"]

    G["GitHub Actions<br/>Mon-Fri 18:00 WAT"] -. orchestrates .-> A
    G -. orchestrates .-> C
    G -. orchestrates .-> B
    G -. orchestrates .-> T
```

| Layer | Tool | Role |
|---|---|---|
| Ingestion | Python (`yfinance`, `requests`, `psycopg2`) | Stock prices, exchange rates, company list, loaded straight into Neon |
| Ingestion | Airbyte Cloud (native Google Sheets source) | Trade log, copied from Google Sheets into Neon |
| Warehouse | Neon (serverless Postgres) | Raw tables in `public`, dbt models in `analytics` |
| Transformation | dbt Core 1.10 (`dbt-postgres`) | Cleans each source, joins them, calculates value and gain/loss in USD and NGN |
| Visualisation | Metabase (self-hosted via Docker) | Four required charts on one dashboard |
| Orchestration | GitHub Actions | One daily workflow, fails loudly on any broken step |

---

## Data sources

| Source | Method | Raw table in Neon | Notes |
|---|---|---|---|
| Stock prices | `get-tickers.py` using `yfinance` | `stock_prices_vsc` | 8 tickers: AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, TSLA, JNJ. Adjusted daily close, in USD |
| Trade log | Google Sheet, then Airbyte native Google Sheets source | `trade_log` | Date, ticker, shares, price paid (USD). Realistic imaginary portfolio: 8 trades, one per ticker, January 2026 |
| Exchange rates | `get-exchange-rates.py` using the apilayer Exchange Rates Data API | `exchange_rates_vsc` | Full history from 2026-01-01 on the first run, then the latest rate each day. Missing weekdays are filled automatically |
| Company reference | `get-company.py` | `company_vsc` | Ticker, company name and sector. A small hand-written lookup table |

Each Python script upserts into Neon (safe to re-run, no duplicates) and also saves a local CSV copy.

---

## Data model

![ERD](images/ERD.png)

### dbt layers (schema `analytics`)

```
sources (raw)            staging (tables)            intermediate (view)        mart (table)
stock_prices_vsc   --->  stg_stock_prices   --+
exchange_rates_vsc --->  stg_exchange_rates  -+--> int_daily_positions ---> mart_portfolio_value
company_vsc        --->  stg_company         -+
trade_log          --->  stg_trades          --+
```

| Layer | Model | Job |
|---|---|---|
| Staging | `stg_*` (one per source) | Rename, cast types, standardise tickers. No joins, no maths |
| Intermediate | `int_daily_positions` | For each day and ticker: shares held and cost basis (all purchases up to that date) |
| Mart | `mart_portfolio_value` | The deliverable. One row per date per ticker, with USD and NGN values and gain/loss |

### How values are calculated

| Column | Formula |
|---|---|
| `shares_held` | Sum of shares bought on or before the date |
| `market_value_usd` | `shares_held x close_price` |
| `cost_basis_usd` | Sum of `shares x price_paid` |
| `unrealized_gain_usd` | `market_value_usd - cost_basis_usd` |
| `market_value_ngn` | `market_value_usd x USD/NGN rate on that date` |
| `cost_basis_ngn` | Sum of `shares x price_paid x USD/NGN rate on the purchase date` |
| `unrealized_gain_ngn` | `market_value_ngn - cost_basis_ngn` |

Because the NGN cost is converted at the rate on each purchase date, **the NGN return includes the effect of the naira moving since purchase**, so it can differ from the USD return. The mart also provides `avg_cost_usd`, `unrealized_gain_pct`, `unrealized_gain_pct_ngn`, `gain_loss_status`, `company_name` and `sector`.

### Tests (17 dbt data tests)

- `not_null` on prices, rates, shares, trade fields and key mart columns
- `unique` on `rate_date` and on `stg_company.ticker`
- `unique_combination_of_columns` on `(price_date, ticker)` in the staging prices and the mart
- `relationships`: every traded ticker exists in `stg_company`, and every trade date has an exchange rate

---

## Orchestration

One workflow, `.github/workflows/pipeline.yml`, runs **Monday to Friday at 17:00 UTC (18:00 WAT)**. It can also be started manually from the Actions tab (`workflow_dispatch`).

```
1. python get-tickers.py          stock prices  -> Neon
2. python get-exchange-rates.py   exchange rates -> Neon
3. python trigger_airbyte.py      start the Airbyte sync, wait until it succeeds
4. dbt deps
5. dbt run                        rebuild staging, intermediate, mart
6. dbt test                       data quality checks
```

Steps run in order and the workflow stops at the first failure, so dbt never runs on stale or partial data. `concurrency` prevents overlapping runs. Credentials come from GitHub Actions secrets, never from the repo.

![Successful workflow run](images/pipeline-run.png)

---

## Visualisation (Metabase)

All charts read from `analytics.mart_portfolio_value`.

| Question | Chart |
|---|---|
| Portfolio value over time | Line: amount invested vs market value |
| Gain/loss by position | Bar, latest day, gains green and losses red |
| Current allocation | Donut by ticker |
| Portfolio value in NGN vs USD | Two line charts side by side (kept separate because naira values are about 1,400 times larger) |

---

## Repository structure

```
portfolio-analytics/
├── .github/workflows/pipeline.yml     daily orchestration
├── dbt/
│   ├── dbt_project.yml, packages.yml, profiles.yml, package-lock.yml
│   └── models/
│       ├── staging/                   sources.yml, schema.yml, stg_*.sql
│       ├── intermediate/              int_daily_positions.sql
│       └── marts/                     schema.yml, mart_portfolio_value.sql
├── images/                            screenshots and ERD
├── get-tickers.py                     stock prices
├── get-exchange-rates.py              exchange rates
├── get-company.py                     company reference table
├── generate-trade-log-single-run.py   builds trade_log.csv for the Google Sheet
├── trigger_airbyte.py                 triggers and waits for the Airbyte sync
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Python environment

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file (already in `.gitignore`) with no spaces around `=`:

```
neon_connection_string="postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
neon_host="..."
neon_user="..."
neon_password="..."
neon_db="..."
apilayer_key="..."
AIRBYTE_CLIENT_ID="..."
AIRBYTE_CLIENT_SECRET="..."
AIRBYTE_CONNECTION_IDS="..."
```

The Python scripts use `neon_connection_string`. dbt uses the four separate `neon_*` values.

### 3. Load the data

```bash
python get-company.py
python get-tickers.py
python get-exchange-rates.py
```

Import `trade_log.csv` into Google Sheets (header row: `date, ticker, shares, price_paid`), then run the Airbyte connection once.

### 4. Airbyte

Source: Google Sheets (native). Destination: Postgres, pointed at Neon with SSL on. Set the connection schedule to **Manual**, because GitHub Actions triggers it.

### 5. dbt

```bash
set -a; source .env; set +a
cd dbt
dbt deps --profiles-dir .
dbt run  --profiles-dir .
dbt test --profiles-dir .
```

### 6. Metabase

```bash
docker run -d -p 3000:3000 \
  -v ~/investment-portfolio-metabase-data:/metabase-data \
  -e "MB_DB_FILE=/metabase-data/metabase.db" \
  --name investment-portfolio-metabase metabase/metabase
```

Open http://localhost:3000, add the Neon database (PostgreSQL, SSL on), and build the charts on `analytics.mart_portfolio_value`.

### 7. GitHub Actions secrets

Settings, Secrets and variables, Actions, then add: `NEON_CONNECTION_STRING`, `NEON_HOST`, `NEON_USER`, `NEON_PASSWORD`, `NEON_DB`, `APILAYER_KEY`, `AIRBYTE_CLIENT_ID`, `AIRBYTE_CLIENT_SECRET`, `AIRBYTE_CONNECTION_IDS`