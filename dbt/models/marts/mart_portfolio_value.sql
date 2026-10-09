SELECT
    pos.price_date,
    pos.ticker,
    pos.shares_held,
    pos.close_price,
    pos.cost_basis_usd,
    pos.market_value_usd,
    pos.unrealized_gain_usd,
    r.usd_ngn_rate,
    pos.market_value_usd    * r.usd_ngn_rate AS market_value_ngn,
    pos.unrealized_gain_usd * r.usd_ngn_rate AS unrealized_gain_ngn
FROM {{ ref('int_daily_positions') }} pos
LEFT JOIN {{ ref('stg_exchange_rates') }} r
  ON r.rate_date = pos.price_date