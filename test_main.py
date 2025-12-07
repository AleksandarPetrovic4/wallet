import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from db import get_session
from main import app
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    # Use in-memory SQLite DB for tests
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_api(client: TestClient):
    response = client.post(
        "/wallet/add/eur/50", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Added 50.0 EUR to your wallet"

    response = client.post(
        "/wallet/sub/eur/50", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Subtracted 50.0 EUR from your wallet"

    response = client.post(
        "/wallet/set/chf/30", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Set CHF to 30.0 in your wallet"

    response = client.get("/wallet", headers={"Authorization": "Bearer test_user1"})
    assert response.status_code == 200
    data = response.json()

    # We can't assert exact values, as they depend on current exchange rate
    # Just confirm we have 0 EUR and 3 total rows in response
    assert len(data) == 3
    assert "0.0 PLN for EUR" in data


def test_invalid_api_calls(client: TestClient):
    # Subtract more than you have
    response = client.post(
        "/wallet/sub/chf/10", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 400

    # Send negative amount
    response = client.post(
        "/wallet/set/chf/-5", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 422

    response = client.post(
        "/wallet/add/chf/-5", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 422

    response = client.post(
        "/wallet/sub/chf/-5", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 422

    # Add invalid currency
    response = client.post(
        "/wallet/add/rsd/50", headers={"Authorization": "Bearer test_user1"}
    )
    assert response.status_code == 400


def test_auth(client: TestClient):
    response = client.post("/wallet/add/eur/50")
    assert response.status_code == 401
    response = client.post("/wallet/set/eur/50")
    assert response.status_code == 401
    response = client.post("/wallet/sub/eur/50")
    assert response.status_code == 401
    response = client.get("/wallet")
    assert response.status_code == 401
