select
    pos.price_date,
    pos.ticker,
    c.company_name,
    c.sector,
    pos.shares_held,
    round(pos.cost_basis_usd / nullif(pos.shares_held, 0), 4)            as avg_cost_usd,
    pos.close_price,
    pos.cost_basis_usd,
    pos.market_value_usd,
    pos.unrealized_gain_usd,
    round(pos.unrealized_gain_usd
          / nullif(pos.cost_basis_usd, 0) * 100, 2)                      as unrealized_gain_pct,
    case
        when pos.unrealized_gain_usd > 0 then 'gain'
        when pos.unrealized_gain_usd < 0 then 'loss'
        else 'flat'
    end                                                                   as gain_loss_status,
    r.usd_ngn_rate,
    pos.cost_basis_ngn,
    pos.market_value_usd * r.usd_ngn_rate                                 as market_value_ngn,
    pos.market_value_usd * r.usd_ngn_rate - pos.cost_basis_ngn            as unrealized_gain_ngn,
    round((pos.market_value_usd * r.usd_ngn_rate - pos.cost_basis_ngn)
          / nullif(pos.cost_basis_ngn, 0) * 100, 2)                       as unrealized_gain_pct_ngn
from {{ ref('int_daily_positions') }} pos
left join {{ ref('stg_exchange_rates') }} r
  on r.rate_date = pos.price_date
left join {{ ref('stg_company') }} c
  on c.ticker = pos.ticker