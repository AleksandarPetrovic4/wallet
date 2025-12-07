### About: 
#### General
The app uses FastAPI framework and pyton >= 3.10
#### Database
By default, the application uses SQLite database which is stored into database.db file in project root folder. 
It can use PostgreSQL as well, by specifying full DB URL connection string in config.ini
#### NBP API
* When contacting NBP API, we're cashing results and calling API again after 5 minutes
* NBP API endpoint ```https://api.nbp.pl/api/exchangerates/tables/c/``` has only 13 currencies, so we're limited to USD, AUD, CAD, EUR, HUF, CHF, GBP, JPY, CZK, DKK, NOK, SEK and XDR. If you try entering eg. RSD as currency, API will return error 400. 
* There is another API endpoint ```https://api.nbp.pl/api/exchangerates/tables/a/``` which contains all currencies, but that table only contains "Mid" price, while instructions said to use "Ask" price (which is only present in previous table)
#### Authentication
All API endpoints require Authorization header.<br/>
However, user management seemed to be out of scope for this exercise, so you can send Authentication header with value "Bearer USERNAME" and that is enough to be authenticated with that username<br/>
In swagger, you can authenticate with any username and password and resulting Bearer token is just raw username


### How to run:
#### In Virtual Environment
Create virtual env (you'll need python >= 3.10):
```
python -m venv .
```
Activate environment:
```
source .venv/bin/activate
```
Install dependencies:
```
pip install -r requirements.txt
```
or ``` pip install -r requirements-dev.txt ``` if you want to run tests (with ``` python -m pytest ```)
 
The application can optionally use PostgreSQL, so it has psycopg2 in its dependencies.<br/>
If you get error "Error: pg_config executable not found." when running above command, you can remove psycopg2 from requirements.txt and just use SQLite DB
<br/><br/>
Run project:
```
fastapi run main.py
```
#### In docker container
Create docker image:
```
docker build -t wallet .
```
Run docker container:
```
docker run -d --name wallet -p 80:80 wallet
```
If you are using SQLite, docker should work out of the box.<br/> 
If you specify PostgreSQL connection in config.ini (before building docker image), you need to make sure PostgreSQL server is reachable from inside docker container.

