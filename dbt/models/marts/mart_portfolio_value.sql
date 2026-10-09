SELECT
    pos.price_date,
    pos.ticker,
    c.company_name,
    c.sector,
    pos.shares_held,
    round(pos.cost_basis_usd / nullif(pos.shares_held, 0), 4) AS avg_cost_usd,
    pos.close_price,
    pos.cost_basis_usd,
    pos.market_value_usd,
    pos.unrealized_gain_usd,
    round(pos.unrealized_gain_usd
          / nullif(pos.cost_basis_usd, 0) * 100, 2) AS unrealized_gain_pct,
    CASE
        WHEN pos.unrealized_gain_usd > 0 THEN 'gain'
        WHEN pos.unrealized_gain_usd < 0 THEN 'loss'
        ELSE 'flat'
    END                                             AS gain_loss_status,
    r.usd_ngn_rate,
    pos.cost_basis_usd      * r.usd_ngn_rate        AS cost_basis_ngn,
    pos.market_value_usd    * r.usd_ngn_rate        AS market_value_ngn,
    pos.unrealized_gain_usd * r.usd_ngn_rate        AS unrealized_gain_ngn
FROM {{ ref('int_daily_positions') }} pos
LEFT JOIN {{ ref('stg_exchange_rates') }} r
  ON r.rate_date = pos.price_date
LEFT JOIN {{ ref('stg_company') }} c
  ON c.ticker = pos.ticker