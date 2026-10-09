select
    pos.price_date,
    pos.ticker,
    pos.shares_held,
    pos.close_price,
    pos.cost_basis_usd,
    pos.market_value_usd,
    pos.unrealized_gain_usd,
    r.usd_ngn_rate,
    pos.market_value_usd    * r.usd_ngn_rate as market_value_ngn,
    pos.unrealized_gain_usd * r.usd_ngn_rate as unrealized_gain_ngn
from {{ ref('int_daily_positions') }} pos
left join {{ ref('stg_exchange_rates') }} r
  on r.rate_date = pos.price_date