select
    price_date::date        as price_date,
    upper(trim(ticker))     as ticker,
    close_price::numeric    as close_price
from {{ source('python_ingest', 'stock_prices_vsc') }}