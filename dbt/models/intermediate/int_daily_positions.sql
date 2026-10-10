select
    p.price_date,
    p.ticker,
    p.close_price,
    sum(t.shares)                                         as shares_held,
    sum(t.shares * t.price_paid)                          as cost_basis_usd,
    sum(t.shares * t.price_paid * tr.usd_ngn_rate)        as cost_basis_ngn,
    sum(t.shares) * p.close_price                         as market_value_usd,
    sum(t.shares) * p.close_price
        - sum(t.shares * t.price_paid)                    as unrealized_gain_usd
from {{ ref('stg_stock_prices') }} p
join {{ ref('stg_trades') }} t
  on t.ticker = p.ticker
 and t.trade_date <= p.price_date
left join {{ ref('stg_exchange_rates') }} tr
  on tr.rate_date = t.trade_date
group by p.price_date, p.ticker, p.close_price