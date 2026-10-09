select
    rate_date::date         as rate_date,
    usd_ngn_rate::numeric   as usd_ngn_rate,
    is_filled
from {{ source('python_ingest', 'exchange_rates_vsc') }}