SELECT
    p.price_date,
    p.ticker,
    p.close_price,
    sum(t.shares) AS shares_held,
    sum(t.shares * t.price_paid) AS cost_basis_usd,
    sum(t.shares) * p.close_price AS market_value_usd,
    sum(t.shares) * p.close_price
        - sum(t.shares * t.price_paid) AS unrealized_gain_usd
FROM {{ ref('stg_stock_prices') }} p
JOIN {{ ref('stg_trades') }} t
  ON t.ticker = p.ticker
 AND t.trade_date <= p.price_date
GROUP BY p.price_date, p.ticker, p.close_price