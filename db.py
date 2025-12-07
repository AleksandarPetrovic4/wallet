from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Field, Session


class Wallet(SQLModel, table=True):
    owner: str = Field(primary_key=True, index=True)
    amount: float = Field()
    currency: str = Field(primary_key=True, index=True)


# Default DB, can be overridden in config.ini
sqlite_url = "sqlite:///database.db"

# Try to read DATABASE_URL from config.ini
config_object = ConfigParser()
config_object.read("config.ini")
db_info = config_object["DBCONFIG"]

db_url = db_info.get("DATABASE_URL", sqlite_url)
engine = create_engine(db_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
