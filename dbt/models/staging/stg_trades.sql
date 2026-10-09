select distinct
    "date"::date            as trade_date,
    upper(trim(ticker))     as ticker,
    shares::numeric         as shares,
    price_paid::numeric     as price_paid
from {{ source('airbyte', 'trade_log') }}
where ticker is not null