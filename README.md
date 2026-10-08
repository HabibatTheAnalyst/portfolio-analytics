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
