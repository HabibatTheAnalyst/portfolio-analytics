SELECT distinct
    "date"::date            AS trade_date,
    upper(trim(ticker))     AS ticker,
    shares::numeric         AS shares,
    price_paid::numeric     AS price_paid
FROM {{ source('airbyte', 'trade_log') }}
WHERE ticker IS NOT NULL