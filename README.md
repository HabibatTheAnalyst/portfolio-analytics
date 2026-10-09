# portfolio-analytics
Tracking investment value in USD and NGN


clone repo from github
- git clone {https-link} give-the-repo-a-name


Q1 - PERFORMANCE
Q2 - PERFORMANCE
Q3 -?

How did i setup neon?
Steps taken


setup airbyte
- connect trade logs in google sheet via native(created and handled by airbyte) connection in airbyte
- go to connections tab, click on googlesheet, input the google sheet url and depending on how large the file is, set bacth upload.

- then i get redirected to destination page
    - here, select postgres because there's no "neon"
    - then input neon's connection details
    - using the connection string, you get below to be filled in destination page in airbyte
        Host	ep-xxxx-pooler.us-east-2.aws.neon.tech (everything after @ and before /)
        Port	5432
        Database name	mydb (after the /, before the ?)
        Username	investment_portfolio_owner
        Password	after : before @
        SSL mode	require
        SSH Tunnel Method   No Tunnel
    - you get taken to the next page to set scheme
    - then configure connections


Exchange rata data
UPLOAD TO NEON VIA AIRBYTE USING CUSTOM CONNECTION

Prerequisites
    - Exchange Rates API account
    - API Access Key
Setup Guide

step 0: search for "Exchange Rates API" connection in Airbyte connnection/marketplace

Step 1: Set up Exchange Rates API
    - Create an account with Exchange Rates API. https://marketplace.apilayer.com/exchangerates_data-api#pricing 
    - Navigate to the Exchange Rates API Dashboard to find your API Access Key.

NOTE: If you have a free subscription plan, you will have two limitations to the plan: 1. Limit of 1,000 API calls per month 2. You won't be able to specify the base parameter, meaning that you will be only be allowed to use the default base value which is EUR.

Step 2: Set up the Exchange Rates connector in Airbyte
    - Enter a Name for your source.
    - Enter your API key as the access_key from the prerequisites.
    - Enter the Start Date in YYYY-MM-DD format. The data added on and after this date will be replicated.
    (Optional) Enter a base currency. For those on the free plan, EUR is the only option available. If none are specified, EUR will be used.
    - Click Set up source.

Step 3: same destination as the one used for google sheet. 
    - Schedule type - cron set to run mon - fri 6pm (0 0 18 ? * MON-FRI)


    issues - date ids not returning histprical data even after specifying startdate
            - its returning EUR rate not USD 
            - thats the defualt currency on free plan
    resolution - used python script instead of airbyte

TRANSFORMATION
- create the dbt folder and files for transformation 
- set the destination (neon in this case) credentials in .env
- run `set -a; source .env; set +a` in terminal to load the credentials into the terminal session so dbt can read them with env_var(...). `YOU WILL HAVE TO RE RUN THIS FOR EVERY NEW TERMINAL WINDOW` 
- then run `dbt deps --profiles-dir .` it downloads the packages listed in packages.yml (here, dbt_utils) into a dbt_packages/ folder in your project. Without it, dbt test fails with an error that the macro can't be found. You only need to run it once per project, plus again if you change packages.yml or clone the project onto a new machine. You don't need it before every dbt run. 

        - multiple files including logs where created after running above

- then run `dbt debug --profiles-dir .` checks that dbt is set up correctly.


AFTER STAGING
- run dbt `run --select staging --profiles-dir .` to chec that all staged files ran
- then move to intermediate and marts. 
- once done with marts and intermediate, run `dbt run --profiles-dir .` and `dbt test --profiles-dir .`

`dbt run` should report 5 successful models (3 staging views, 1 intermediate view, 1 mart table).
`dbt test` should pass everything. A failing test means a real data problem. The most likely one is usd_ngn_rate being null on early dates, which means the exchange rates don't cover every price date.


VISUALIZATION
- to link metabase to docker, run in terminal 
        docker run -d -p 3000:3000 \
        -v ~/investment-portfolio-metabase-data:/metabase-data \
        -e "MB_DB_FILE=/metabase-data/metabase.db" \
        --name investment-portfolio-metabase metabase/metabase

- When you see a line saying Metabase is initialised or similar, open http://localhost:3000
- then create admin account
- then connect Metabase to Neon
- create charts and dashboards