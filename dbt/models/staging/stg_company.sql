SELECT
    upper(trim(ticker))   AS ticker,
    company_name,
    sector
FROM {{ source('python_ingest', 'company_vsc') }}