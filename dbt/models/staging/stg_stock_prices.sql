SELECT
    price_date::date        AS price_date,
    upper(trim(ticker))     AS ticker,
    close_price::numeric    AS close_price
FROM {{ source('python_ingest', 'stock_prices_vsc') }}