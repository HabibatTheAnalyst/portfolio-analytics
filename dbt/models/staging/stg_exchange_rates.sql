SELECT
    rate_date::date         AS rate_date,
    usd_ngn_rate::numeric   AS usd_ngn_rate,
    is_filled
FROM {{ source('python_ingest', 'exchange_rates_vsc') }}