from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session, select
from db import get_session, create_db_and_tables, Wallet
from exchange import Exchange


SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
exchange = Exchange()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def extract_user_from_token(token: str) -> str:
    # We're not decoding anything, since access_token is just raw username
    return token


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # access_token will just be raw username
    return {"access_token": form_data.username, "token_type": "bearer"}


@app.get("/wallet/")
async def get(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    """
    :param session: Auto inserted dependency
    :param token: Auto inserted dependency
    :return: Content of users wallet (converted to PLN)
    """
    owner = extract_user_from_token(token)
    wallets = session.exec(select(Wallet).filter_by(owner=owner)).all()
    response = []
    total = 0
    for wallet in wallets:
        in_pln = exchange.to_pln(wallet)
        total += in_pln
        response.append(f"{round(in_pln, 2)} PLN for {wallet.currency}")
    response.append(f"{round(total, 2)} PLN total")
    return response


@app.post("/wallet/add/{currency}/{amount}")
async def add_to_wallet(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
    currency: str,
    amount: Annotated[float, Path(title="Amount to add", ge=0)],
):
    """
    Add an amount of currency to your existing wallet
    :param session: Auto inserted dependency
    :param token: Auto inserted dependency
    :param currency: Currency to add
    :param amount: amount to add
    :return: OK message, or error 400 if currency is not valid
    """
    owner = extract_user_from_token(token)
    currency = currency.upper()
    if currency not in exchange.get_exchange_rates():
        raise HTTPException(status_code=400, detail="Invalid currency")
    wallet = session.exec(
        select(Wallet).filter_by(owner=owner, currency=currency)
    ).one_or_none()
    if not wallet:
        wallet = Wallet(owner=owner, currency=currency, amount=amount)
        session.add(wallet)
    else:
        wallet.amount += amount

    session.commit()
    session.refresh(wallet)
    return {"message": f"Added {amount} {currency} to your wallet"}


@app.post("/wallet/sub/{currency}/{amount}")
async def subtract_from_wallet(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
    currency: str,
    amount: Annotated[float, Path(title="Amount to subtract", ge=0)],
):
    """
    Remove an amount of currency from your existing wallet
    :param session:  Auto inserted dependency
    :param token: Auto inserted dependency
    :param currency: Currency to subtract
    :param amount: Amount to subtract
    :return: OK message, or error 400 (if currency is not valid, or you don't have enough money)
    """
    owner = extract_user_from_token(token)
    currency = currency.upper()

    if currency not in exchange.get_exchange_rates():
        raise HTTPException(status_code=400, detail="Invalid currency")
    wallet = session.exec(
        select(Wallet).filter_by(owner=owner, currency=currency)
    ).one_or_none()
    if not wallet:
        raise HTTPException(
            status_code=400, detail=f"You don't have any {currency} in your wallet"
        )
    else:
        wallet.amount -= amount
        if wallet.amount < 0:
            raise HTTPException(
                status_code=400,
                detail=f"You don't have enough {currency} in your wallet",
            )

    session.commit()
    session.refresh(wallet)
    return {"message": f"Subtracted {amount} {currency} from your wallet"}


@app.post("/wallet/set/{currency}/{amount}")
async def set_wallet(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
    currency: str,
    amount: Annotated[float, Path(title="Amount to set", ge=0)],
):
    """
    Set an amount of currency in your wallet (doesn't take into account how much you had before)
    :param session: Auto inserted dependency
    :param token: Auto inserted dependency
    :param currency: Currency to set
    :param amount: Amount to set
    :return: OK message, or error 400 if currency is not valid
    """
    owner = extract_user_from_token(token)
    currency = currency.upper()
    if currency not in exchange.get_exchange_rates():
        raise HTTPException(status_code=400, detail="Invalid currency")
    wallet = session.exec(
        select(Wallet).filter_by(owner=owner, currency=currency)
    ).one_or_none()
    if not wallet:
        wallet = Wallet(owner=owner, currency=currency, amount=amount)
        session.add(wallet)
    else:
        wallet.amount = amount

    session.commit()
    session.refresh(wallet)
    return {"message": f"Set {currency} to {amount} in your wallet"}
