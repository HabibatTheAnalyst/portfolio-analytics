# portfolio-analytics
Tracking investment value in USD and NGN

This is a personal portfolio data platform. Three different sources are ingested into a Neon (Postgres) warehouse, transformed with dbt Core into one analytics table, visualised in Metabase hosted by Docker, and refreshed automatically every weekday by GitHub Actions.

---

### Pipeline
Source                                                   Destination            Staging          Orchestration          
Exchange rates                     (Python Ingest) --->                         
Stock_prices                       (Python Ingest) --->    Neon      --->     dbt Core    --->    Github Action       
Trade_log      ---> Google Sheet         (Airbyte) --->                           |
                                                                            Neon (Staged files)   --->   Metabase (Visualization)

---

### Steps 
#### 1.
- Get data via script and manual entry
- Setup `Neon` by creating project and database and specifying schema
- Setup `Airbyte`
    - Connect trade logs in google sheet via native(created and handled by Airbyte) connection in `Airbyte`
    - Go to `connections tab` to set the `source`, click on Google Sheet, input the Google Sheet url and depending on how large the file is, set bacth upload.
    - Then you get redirected to the `destination page`
        - Here, select `postgres` because there's no "Neon" because Airbyte builds its connectors for database engines, not for companies that host them. Neon is standard Postgres running in the cloud, so it speaks the same protocol as any other Postgres database, and Airbyte's Postgres destination connects to it with no special handling.
        - Then input Neon's connection details using the connection string gotten by clicking the green `connection` botton.The string is to be used in destination page in airbyte to fill below infomations
            Host	ep-xxxx-pooler.us-east-2.aws.neon.tech `(everything after @ and before /)`
            Port	5432
            Database name	mydb `(after the /, before the ?)`
            Username	investment_portfolio_owner
            Password	after `: before @`
            SSL mode	require
            SSH Tunnel Method   No Tunnel
        - You get taken to the next page to set scheme
        - Then configure connections

---
#### 2.
- To upload data to Neon via Airbyte' custom connection `(Exchange rata data)`
    - Prerequisites
        You need:
            * Exchange Rates API account
            * API Access Key

    - Setup Guide
    Step 0: search for `Exchange Rates API` connection in Airbyte' `connnection/marketplace`
    Step 1: Set up Exchange Rates API
        - Create an account with Exchange Rates API. {link}[https://marketplace.apilayer.com/exchangerates_data-api#pricing] 
        - Navigate to the Exchange Rates API Dashboard to find your `API Access Key`.

        NOTE: If you have a free subscription plan, you will have two limitations to the plan: 
            1. Limit of 1,000 API calls per month 
            2. You won't be able to specify the base parameter, meaning that you will be only be allowed to use the default base value which is EUR.

    Step 2: Set up the Exchange Rates connector in Airbyte
        - Enter a Name for your source.
        - Enter your API key as the `access_key` from the prerequisites.
        - Enter the Start Date in YYYY-MM-DD format. The data added on and after this date will be replicated.
        - Enter a base currency. 
        - Click Set up source.
        
        NOTE: For those on the free plan, EUR is the only option available. If none are specified, EUR will be used.
        
    Step 3: You will be redirected to the destication page
        - Since the destination is `Neon`, select the same destination as the one used for Google Sheet
        - Schedule type - cron set to run mon - fri 6pm (0 0 18 ? * MON-FRI)

        * Issues to Note - date ids not returning histprical data even after specifying startdate. Getting data via airbyte, only current date data is returned
        * My Rresolution to this issue for this project - used python script for the same api link instead of Airbyte

---
#### 3. 
Transformation / Staging using dbt Core
- Create the dbt folder and files for transformation 
- Set the destination (`Neon` in this case) credentials in `.env`
- Run `set -a; source .env; set +a` in terminal to load the credentials into the terminal session so dbt can read them with env_var(...)
    NOTE:
    - You have to run above while on the dbt file so `cd dbt` before running
    - `YOU WILL HAVE TO RE RUN THIS FOR EVERY NEW TERMINAL WINDOW` 

- Then run `dbt deps --profiles-dir .` it downloads the packages listed in packages.yml into a `dbt_packages/` folder in your project. Without it, dbt test fails with an error `that the macro can't be found`. You only need to run it once per project, plus again if you change packages.yml or clone the project onto a new machine. You don't need it before every dbt run. 
    NOTE:
    - Multiple files including logs where created after running above

- Then run `dbt debug --profiles-dir .` checks that dbt is set up correctly.

After Staging
- Run dbt `run --select staging --profiles-dir .` to checK that all staged files ran
- Then move to `intermediate` and `marts` folders 
- Once done with marts and intermediate, run `dbt run --profiles-dir .` and `dbt test --profiles-dir .`

NOTE:
A.
`dbt run` should report 5 successful models (3 staging views, 1 intermediate view, 1 mart table).
`dbt test` should pass everything. A failing test means a real data problem. The most likely one is usd_ngn_rate being null on early dates, which means the exchange rates don't cover every price date 

B.
This was put into consideration when generating the data. The code checks for blank dates and gets the data for those and/or fills blanks (holidays) with the previous dates data. Weekends are skipped

---
### 4.
Visualisation
- To link metabase to docker, run in terminal 
        docker run -d -p 3000:3000 \
        -v ~/investment-portfolio-metabase-data:/metabase-data \
        -e "MB_DB_FILE=/metabase-data/metabase.db" \
        --name investment-portfolio-metabase metabase/metabase
    NB: `investment-portfolio-metabase` is the name that appears in Docker
- When you see a line saying Metabase is initialised or similar, open http://localhost:3000 or click on the embeded linked port number(3000:3000 in this case)
- Then create admin account
- Connect Metabase to Neon
- Create charts and dashboards

---
#### 5.
How to create Airbyte credential ids for GitHub automation access
- Go to airbyte
- Then settings
- Then click on the `user profile` name at the bottom left
- Then clcik/go to `applications`
- Then create create application    

---
#### 6.
Create GitHub automation
- Go to GitHub
- Go to the Repository 
- Settings
- Secrets and Variables
- Actions
- Then create new secret access by clciking on `new repository secret`

---
## Good to know tips while working on this project
- To clone repo from github use `git clone {https-link} give-the-repo-a-name`


Q1 - PERFORMANCE
Q2 - PERFORMANCE
Q3 -?